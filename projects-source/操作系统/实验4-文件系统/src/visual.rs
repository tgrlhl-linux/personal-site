use crate::disk::{Disk, BLOCK_SIZE, UFD_START, DATA_START, SUPER_BLOCK, NUM_BLOCKS};
use crate::fs::{bytes_to_struct, SuperBlock};

#[derive(Debug, Clone, PartialEq)]
pub enum BlockStatus {
    Boot,
    SuperBlock,
    MFD,
    UFD,
    FileData,
    Free,
}

#[derive(Debug, Clone)]
pub struct BlockInfo {
    pub block_num: usize,
    pub status: BlockStatus,
    pub label: String,
}

#[derive(Debug, Clone)]
pub struct DiskState {
    pub blocks: Vec<BlockInfo>,
    pub total_blocks: usize,
    pub used_blocks: usize,
    pub free_blocks: usize,
    pub block_size: usize,
}

impl DiskState {
    pub fn from_disk(disk: &mut Disk) -> Self {
        let mut blocks = Vec::with_capacity(disk.num_blocks);
        let mut used = 0;

        // Read superblock once to get free_blocks count
        let sb_data = disk.read_block(SUPER_BLOCK).unwrap_or_default();
        let sb: SuperBlock = bytes_to_struct(&sb_data);

        for i in 0..disk.num_blocks {
            let (status, label) = match i {
                0 => (BlockStatus::Boot, "Boot".to_string()),
                1 => (BlockStatus::SuperBlock, format!("SuperBlock ({} free)", sb.free_blocks)),
                2 => (BlockStatus::MFD, "MFD".to_string()),
                n if n >= UFD_START && n < DATA_START => {
                    let user_idx = n - UFD_START;
                    (BlockStatus::UFD, format!("UFD-User{}", user_idx))
                }
                n if n >= DATA_START => {
                    // Read actual disk block to determine if it's in use
                    let data = disk.read_block(n).unwrap_or_default();
                    if data.iter().any(|&x| x != 0) {
                        (BlockStatus::FileData, format!("Data{}", n))
                    } else {
                        (BlockStatus::Free, format!("Data{}", n))
                    }
                }
                _ => unreachable!(),
            };
            if status != BlockStatus::Free {
                used += 1;
            }
            blocks.push(BlockInfo {
                block_num: i,
                status,
                label,
            });
        }

        DiskState {
            blocks,
            total_blocks: disk.num_blocks,
            used_blocks: used,
            free_blocks: disk.num_blocks - used,
            block_size: disk.block_size,
        }
    }

    pub fn mark_block_used(&mut self, block_num: usize) {
        if block_num < self.blocks.len() && self.blocks[block_num].status == BlockStatus::Free {
            self.blocks[block_num].status = BlockStatus::FileData;
            self.blocks[block_num].label = format!("FileData{}", block_num);
            self.used_blocks += 1;
            self.free_blocks = self.total_blocks - self.used_blocks;
        }
    }

    pub fn mark_block_free(&mut self, block_num: usize) {
        if block_num < self.blocks.len() {
            self.blocks[block_num].status = BlockStatus::Free;
            self.blocks[block_num].label = format!("Data{}", block_num);
            self.used_blocks -= 1;
            self.free_blocks = self.total_blocks - self.used_blocks;
        }
    }
}

impl Default for DiskState {
    fn default() -> Self {
        let mut blocks = Vec::with_capacity(NUM_BLOCKS);
        for i in 0..NUM_BLOCKS {
            blocks.push(BlockInfo {
                block_num: i,
                status: BlockStatus::Free,
                label: format!("Data{}", i),
            });
        }
        DiskState {
            blocks,
            total_blocks: NUM_BLOCKS,
            used_blocks: 0,
            free_blocks: NUM_BLOCKS,
            block_size: BLOCK_SIZE,
        }
    }
}
