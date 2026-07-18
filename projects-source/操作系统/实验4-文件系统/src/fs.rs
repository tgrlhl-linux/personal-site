use crate::disk::{Disk, BLOCK_SIZE, SUPER_BLOCK, MFD_BLOCK, UFD_START, DATA_START};
use std::time::{SystemTime, UNIX_EPOCH};

pub const MAX_FILENAME: usize = 28;
pub const MAX_PASSWORD: usize = 16;
// Each DirEntry = 64 bytes, block = 1024 bytes
// MFD: 4(user_count) + 4(padding) + N*64 <= 1024 → N=15
// UFD: N*64 <= 1024 → N=16
pub const MAX_USERS: usize = 15;
pub const MAX_DIR_ENTRIES: usize = 15;
pub const MAGIC_NUMBER: i32 = 0x1E;

// ── Data Structures ──────────────────────────────────────────

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct DirEntry {
    pub name: [u8; MAX_FILENAME],
    pub type_: i32,
    pub start_block: i32,
    pub size: i32,
    pub password: [u8; MAX_PASSWORD],
    pub create_time: i64,
}

impl DirEntry {
    pub fn new(name: &str, type_: i32, password: &str) -> Self {
        let mut entry = DirEntry {
            name: [0u8; MAX_FILENAME],
            type_,
            start_block: -1,
            size: 0,
            password: [0u8; MAX_PASSWORD],
            create_time: SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_secs() as i64,
        };
        let name_bytes = name.as_bytes();
        let len = name_bytes.len().min(MAX_FILENAME - 1);
        entry.name[..len].copy_from_slice(&name_bytes[..len]);
        let pw_bytes = password.as_bytes();
        let pw_len = pw_bytes.len().min(MAX_PASSWORD - 1);
        entry.password[..pw_len].copy_from_slice(&pw_bytes[..pw_len]);
        entry
    }

    pub fn name_str(&self) -> String {
        let end = self.name.iter().position(|&b| b == 0).unwrap_or(self.name.len());
        String::from_utf8_lossy(&self.name[..end]).to_string()
    }

    pub fn password_str(&self) -> String {
        let end = self.password.iter().position(|&b| b == 0).unwrap_or(self.password.len());
        String::from_utf8_lossy(&self.password[..end]).to_string()
    }

    pub fn is_empty(&self) -> bool {
        self.name[0] == 0 || self.name_str().is_empty()
    }
}

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct SuperBlock {
    pub magic_number: i32,
    pub total_blocks: i32,
    pub free_blocks: i32,
    pub mfd_block: i32,
    pub block_size: i32,
}

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct MasterDirectory {
    pub user_count: i32,
    pub users: [DirEntry; MAX_USERS],
}

#[derive(Debug, Clone)]
pub struct Session {
    pub logged_in: bool,
    pub current_user: String,
    pub current_ufd_block: usize,
    pub current_path: String,
    pub disk_path: String,
    pub mounted: bool,
}

impl Session {
    pub fn new() -> Self {
        Session {
            logged_in: false,
            current_user: String::new(),
            current_ufd_block: 0,
            current_path: "/".to_string(),
            disk_path: String::new(),
            mounted: false,
        }
    }
}

// ── Serialization ────────────────────────────────────────────

pub fn struct_to_bytes<T: Sized>(s: &T) -> Vec<u8> {
    let ptr = s as *const T as *const u8;
    let size = std::mem::size_of::<T>();
    let mut bytes = vec![0u8; BLOCK_SIZE];
    unsafe {
        std::ptr::copy_nonoverlapping(ptr, bytes.as_mut_ptr(), size.min(BLOCK_SIZE));
    }
    bytes
}

pub fn bytes_to_struct<T: Sized>(bytes: &[u8]) -> T {
    let size = std::mem::size_of::<T>();
    let mut s: T = unsafe { std::mem::zeroed() };
    unsafe {
        let ptr = &mut s as *mut T as *mut u8;
        std::ptr::copy_nonoverlapping(bytes.as_ptr(), ptr, size.min(bytes.len()));
    }
    s
}

// ── MFD / UFD Helpers ────────────────────────────────────────

pub fn mfd_read(disk: &mut Disk) -> Result<MasterDirectory, String> {
    let data = disk.read_block(MFD_BLOCK)?;
    Ok(bytes_to_struct(&data))
}

pub fn mfd_write(disk: &mut Disk, mfd: &MasterDirectory) -> Result<(), String> {
    disk.write_block(MFD_BLOCK, &struct_to_bytes(mfd))
}

pub fn ufd_read(disk: &mut Disk, user_idx: usize) -> Result<[DirEntry; MAX_DIR_ENTRIES], String> {
    let block_num = UFD_START + user_idx;
    let data = disk.read_block(block_num)?;
    let mut entries = [DirEntry::new("", 0, ""); MAX_DIR_ENTRIES];
    let entry_size = std::mem::size_of::<DirEntry>();
    let max_entries_per_block = data.len() / entry_size;
    let count = MAX_DIR_ENTRIES.min(max_entries_per_block);
    for i in 0..count {
        let offset = i * entry_size;
        let entry_bytes = &data[offset..offset + entry_size];
        entries[i] = bytes_to_struct(entry_bytes);
    }
    Ok(entries)
}

pub fn ufd_write(disk: &mut Disk, user_idx: usize, entries: &[DirEntry; MAX_DIR_ENTRIES]) -> Result<(), String> {
    let block_num = UFD_START + user_idx;
    let mut block = [0u8; BLOCK_SIZE];
    let entry_size = std::mem::size_of::<DirEntry>();
    let max_entries_per_block = BLOCK_SIZE / entry_size;
    let count = MAX_DIR_ENTRIES.min(max_entries_per_block);
    for i in 0..count {
        let offset = i * entry_size;
        let entry_bytes = struct_to_bytes(&entries[i]);
        block[offset..offset + entry_size].copy_from_slice(&entry_bytes[..entry_size]);
    }
    disk.write_block(block_num, &block)
}

fn find_user(mfd: &MasterDirectory, username: &str) -> Option<usize> {
    for i in 0..mfd.user_count as usize {
        if !mfd.users[i].is_empty() && mfd.users[i].name_str() == username {
            return Some(i);
        }
    }
    None
}

// ── Block Allocation ─────────────────────────────────────────

pub fn alloc_block(disk: &mut Disk) -> Result<usize, String> {
    let sb_data = disk.read_block(SUPER_BLOCK)?;
    let mut sb: SuperBlock = bytes_to_struct(&sb_data);
    if sb.free_blocks <= 0 {
        return Err("No free blocks available".to_string());
    }
    for b in DATA_START..disk.num_blocks {
        let data = disk.read_block(b)?;
        if data.iter().all(|&x| x == 0) {
            sb.free_blocks -= 1;
            disk.write_block(SUPER_BLOCK, &struct_to_bytes(&sb))?;
            return Ok(b);
        }
    }
    Err("No free blocks found".to_string())
}

pub fn free_block(disk: &mut Disk, block_num: usize) -> Result<(), String> {
    if block_num < DATA_START || block_num >= disk.num_blocks {
        return Err(format!("Invalid block number to free: {}", block_num));
    }
    disk.write_block(block_num, &[0u8; BLOCK_SIZE])?;
    let sb_data = disk.read_block(SUPER_BLOCK)?;
    let mut sb: SuperBlock = bytes_to_struct(&sb_data);
    sb.free_blocks += 1;
    disk.write_block(SUPER_BLOCK, &struct_to_bytes(&sb))
}

fn get_current_entries(session: &Session, disk: &mut Disk) -> Result<[DirEntry; MAX_DIR_ENTRIES], String> {
    if !session.logged_in {
        let mfd = mfd_read(disk)?;
        let mut entries = [DirEntry::new("", 0, ""); MAX_DIR_ENTRIES];
        for i in 0..mfd.user_count as usize {
            entries[i] = mfd.users[i];
        }
        return Ok(entries);
    }
    let user_idx = session.current_ufd_block - UFD_START;
    ufd_read(disk, user_idx)
}

fn set_current_entries(session: &Session, disk: &mut Disk, entries: &[DirEntry; MAX_DIR_ENTRIES]) -> Result<(), String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    let user_idx = session.current_ufd_block - UFD_START;
    ufd_write(disk, user_idx, entries)
}

// ── Filesystem Operations ────────────────────────────────────

pub fn format_filesystem(disk: &mut Disk) -> Result<(), String> {
    let sb = SuperBlock {
        magic_number: MAGIC_NUMBER,
        total_blocks: disk.num_blocks as i32,
        free_blocks: (disk.num_blocks - DATA_START) as i32,
        mfd_block: MFD_BLOCK as i32,
        block_size: disk.block_size as i32,
    };
    disk.write_block(SUPER_BLOCK, &struct_to_bytes(&sb))?;

    let mfd = MasterDirectory {
        users: [DirEntry::new("", 0, ""); MAX_USERS],
        user_count: 0,
    };
    disk.write_block(MFD_BLOCK, &struct_to_bytes(&mfd))?;

    let empty_block = [0u8; BLOCK_SIZE];
    for b in UFD_START..disk.num_blocks {
        disk.write_block(b, &empty_block)?;
    }
    Ok(())
}

pub fn mount_filesystem(session: &mut Session, disk: &mut Disk) -> Result<(), String> {
    let sb_data = disk.read_block(SUPER_BLOCK)?;
    let sb: SuperBlock = bytes_to_struct(&sb_data);
    if sb.magic_number != MAGIC_NUMBER {
        return Err("Invalid filesystem: magic number mismatch".to_string());
    }
    session.mounted = true;
    session.logged_in = false;
    session.current_user.clear();
    session.current_path = "/".to_string();
    Ok(())
}

pub fn umount_filesystem(session: &mut Session) {
    session.mounted = false;
    session.logged_in = false;
    session.current_user.clear();
    session.current_path = "/".to_string();
}

// ── User Management ──────────────────────────────────────────

pub fn user_register(disk: &mut Disk, username: &str, password: &str) -> Result<(), String> {
    if username.is_empty() || username.len() > MAX_FILENAME - 1 {
        return Err("Invalid username length".to_string());
    }
    let mut mfd = mfd_read(disk)?;
    if mfd.user_count >= MAX_USERS as i32 {
        return Err("Maximum users reached".to_string());
    }
    if find_user(&mfd, username).is_some() {
        return Err("User already exists".to_string());
    }
    let idx = mfd.user_count as usize;
    mfd.users[idx] = DirEntry::new(username, 0, password);
    mfd.user_count += 1;
    mfd_write(disk, &mfd)?;
    let ufd_block = UFD_START + idx;
    disk.write_block(ufd_block, &[0u8; BLOCK_SIZE])?;
    Ok(())
}

pub fn user_login(session: &mut Session, disk: &mut Disk, username: &str, password: &str) -> Result<(), String> {
    if !session.mounted {
        return Err("No filesystem mounted".to_string());
    }
    let mfd = mfd_read(disk)?;
    let user_idx = find_user(&mfd, username).ok_or_else(|| "User not found".to_string())?;
    if mfd.users[user_idx].password_str() != password {
        return Err("Wrong password".to_string());
    }
    session.logged_in = true;
    session.current_user = username.to_string();
    session.current_ufd_block = UFD_START + user_idx;
    session.current_path = format!("/{}", username);
    Ok(())
}

pub fn user_logout(session: &mut Session) {
    session.logged_in = false;
    session.current_user.clear();
    session.current_path = "/".to_string();
}

// ── Directory Operations ─────────────────────────────────────

pub fn create_directory(session: &Session, disk: &mut Disk, dirname: &str) -> Result<(), String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    if dirname.contains('/') {
        return Err("Directory name cannot contain '/'".to_string());
    }
    let mut entries = get_current_entries(session, disk)?;
    for e in entries.iter() {
        if !e.is_empty() && e.name_str() == dirname {
            return Err("Entry already exists".to_string());
        }
    }
    let slot = entries.iter_mut().find(|e| e.is_empty()).ok_or_else(|| "Directory is full".to_string())?;
    *slot = DirEntry::new(dirname, 0, "");
    set_current_entries(session, disk, &entries)
}

pub fn change_directory(session: &mut Session, disk: &mut Disk, dirname: &str) -> Result<(), String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    if dirname == ".." {
        session.current_path = format!("/{}", session.current_user);
        return Ok(());
    }
    if dirname == "." {
        return Ok(());
    }
    let entries = get_current_entries(session, disk)?;
    entries
        .iter()
        .find(|e| !e.is_empty() && e.name_str() == dirname && e.type_ == 0)
        .ok_or_else(|| format!("Directory '{}' not found", dirname))?;
    session.current_path = format!("{}/{}", session.current_path, dirname);
    Ok(())
}

pub fn list_directory(session: &Session, disk: &mut Disk) -> Result<Vec<(String, String, i32)>, String> {
    let entries = get_current_entries(session, disk)?;
    let mut result = Vec::new();
    for e in entries.iter() {
        if !e.is_empty() {
            let type_str = if e.type_ == 0 { "DIR" } else { "FILE" };
            result.push((e.name_str(), type_str.to_string(), e.size));
        }
    }
    Ok(result)
}

pub fn delete_directory(session: &Session, disk: &mut Disk, dirname: &str) -> Result<(), String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    let mut entries = get_current_entries(session, disk)?;
    let slot = entries
        .iter_mut()
        .find(|e| !e.is_empty() && e.name_str() == dirname && e.type_ == 0)
        .ok_or_else(|| format!("Directory '{}' not found", dirname))?;
    *slot = DirEntry::new("", 0, "");
    set_current_entries(session, disk, &entries)
}

// ── File Operations ──────────────────────────────────────────

pub fn create_file(session: &Session, disk: &mut Disk, filename: &str) -> Result<(), String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    if filename.contains('/') {
        return Err("Filename cannot contain '/'".to_string());
    }
    let mut entries = get_current_entries(session, disk)?;
    for e in entries.iter() {
        if !e.is_empty() && e.name_str() == filename {
            return Err("File already exists".to_string());
        }
    }
    let slot = entries.iter_mut().find(|e| e.is_empty()).ok_or_else(|| "Directory is full".to_string())?;
    *slot = DirEntry::new(filename, 1, "");
    set_current_entries(session, disk, &entries)
}

pub fn delete_file(session: &Session, disk: &mut Disk, filename: &str) -> Result<(), String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    let mut entries = get_current_entries(session, disk)?;
    let idx = entries
        .iter()
        .position(|e| !e.is_empty() && e.name_str() == filename && e.type_ == 1)
        .ok_or_else(|| format!("File '{}' not found", filename))?;

    let mut block = entries[idx].start_block;
    while block >= 0 {
        let data = disk.read_block(block as usize)?;
        let next_block = i32::from_le_bytes(data[..4].try_into().unwrap_or([0; 4]));
        free_block(disk, block as usize)?;
        block = next_block;
    }
    entries[idx] = DirEntry::new("", 0, "");
    set_current_entries(session, disk, &entries)
}

pub fn read_file(session: &Session, disk: &mut Disk, filename: &str) -> Result<Vec<u8>, String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    let entries = get_current_entries(session, disk)?;
    let entry = entries
        .iter()
        .find(|e| !e.is_empty() && e.name_str() == filename && e.type_ == 1)
        .ok_or_else(|| format!("File '{}' not found", filename))?;

    let mut data = Vec::new();
    let mut block = entry.start_block;
    while block >= 0 {
        let block_data = disk.read_block(block as usize)?;
        let next_block = i32::from_le_bytes(block_data[..4].try_into().unwrap_or([0; 4]));
        let remaining = entry.size as usize - data.len();
        let chunk_size = remaining.min(BLOCK_SIZE - 4);
        data.extend_from_slice(&block_data[4..4 + chunk_size]);
        block = next_block;
    }
    Ok(data)
}

pub fn write_file(session: &Session, disk: &mut Disk, filename: &str, data: &[u8]) -> Result<(), String> {
    if !session.logged_in {
        return Err("Not logged in".to_string());
    }
    let mut entries = get_current_entries(session, disk)?;
    let entry_idx = entries
        .iter()
        .position(|e| !e.is_empty() && e.name_str() == filename && e.type_ == 1)
        .ok_or_else(|| format!("File '{}' not found", filename))?;

    // Free old blocks
    let old_block = entries[entry_idx].start_block;
    let mut block = old_block;
    while block >= 0 {
        let block_data = disk.read_block(block as usize)?;
        let next = i32::from_le_bytes(block_data[..4].try_into().unwrap_or([0; 4]));
        free_block(disk, block as usize)?;
        block = next;
    }

    if data.is_empty() {
        entries[entry_idx].start_block = -1;
        entries[entry_idx].size = 0;
        return set_current_entries(session, disk, &entries);
    }

    // Allocate new blocks and chain them
    let mut first_block = -1i32;
    let mut prev_block = -1i32;
    let mut remaining = data;

    while !remaining.is_empty() {
        let b = alloc_block(disk)? as i32;
        if first_block < 0 {
            first_block = b;
        }
        if prev_block >= 0 {
            let mut prev_data = disk.read_block(prev_block as usize)?;
            prev_data[..4].copy_from_slice(&b.to_le_bytes());
            disk.write_block(prev_block as usize, &prev_data)?;
        }
        let chunk_size = remaining.len().min(BLOCK_SIZE - 4);
        let mut block_data = vec![0u8; BLOCK_SIZE];
        block_data[..4].copy_from_slice(&(-1i32).to_le_bytes());
        block_data[4..4 + chunk_size].copy_from_slice(&remaining[..chunk_size]);
        disk.write_block(b as usize, &block_data)?;
        prev_block = b;
        remaining = &remaining[chunk_size..];
    }

    entries[entry_idx].start_block = first_block;
    entries[entry_idx].size = data.len() as i32;
    set_current_entries(session, disk, &entries)
}
