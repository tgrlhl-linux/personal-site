use std::fs::{File, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};

pub const BLOCK_SIZE: usize = 1024;
pub const NUM_BLOCKS: usize = 512;
pub const BOOT_BLOCK: usize = 0;
pub const SUPER_BLOCK: usize = 1;
pub const MFD_BLOCK: usize = 2;
pub const UFD_START: usize = 3;
pub const UFD_END: usize = 34;
pub const DATA_START: usize = 35;

pub struct Disk {
    file: File,
    pub num_blocks: usize,
    pub block_size: usize,
}

impl Disk {
    pub fn new(path: &str) -> Result<Self, String> {
        let file = OpenOptions::new()
            .read(true)
            .write(true)
            .create(true)
            .open(path)
            .map_err(|e| format!("Failed to open disk file: {}", e))?;
        file.set_len((NUM_BLOCKS * BLOCK_SIZE) as u64)
            .map_err(|e| format!("Failed to set disk size: {}", e))?;
        Ok(Disk {
            file,
            num_blocks: NUM_BLOCKS,
            block_size: BLOCK_SIZE,
        })
    }

    pub fn read_block(&mut self, block_num: usize) -> Result<Vec<u8>, String> {
        if block_num >= self.num_blocks {
            return Err(format!("Block {} out of range (max {})", block_num, self.num_blocks));
        }
        let offset = (block_num * self.block_size) as u64;
        self.file
            .seek(SeekFrom::Start(offset))
            .map_err(|e| format!("Seek error: {}", e))?;
        let mut buf = vec![0u8; self.block_size];
        self.file
            .read_exact(&mut buf)
            .map_err(|e| format!("Read error: {}", e))?;
        Ok(buf)
    }

    pub fn write_block(&mut self, block_num: usize, data: &[u8]) -> Result<(), String> {
        if block_num >= self.num_blocks {
            return Err(format!("Block {} out of range (max {})", block_num, self.num_blocks));
        }
        if data.len() != self.block_size {
            return Err(format!("Data size {} != block size {}", data.len(), self.block_size));
        }
        let offset = (block_num * self.block_size) as u64;
        self.file
            .seek(SeekFrom::Start(offset))
            .map_err(|e| format!("Seek error: {}", e))?;
        self.file
            .write_all(data)
            .map_err(|e| format!("Write error: {}", e))?;
        self.file
            .flush()
            .map_err(|e| format!("Flush error: {}", e))?;
        Ok(())
    }
}
