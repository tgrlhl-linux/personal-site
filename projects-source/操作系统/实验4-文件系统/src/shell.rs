use crate::disk::Disk;
use crate::fs::*;
use crate::visual::DiskState;

#[derive(Debug)]
pub enum Command {
    Format { diskname: String },
    Mount { diskname: String },
    Umount,
    Register { username: String, password: String },
    Login { username: String, password: String },
    Logout,
    Mkdir { dirname: String },
    Cd { dirname: String },
    List,
    Rmdir { dirname: String },
    Create { filename: String },
    Delete { filename: String },
    Read { filename: String },
    Write { filename: String, data: String },
    Clear,
    Help,
    Quit,
}

pub fn parse_command(input: &str) -> Result<Command, String> {
    let input = input.trim();
    if input.is_empty() {
        return Err("Empty command".to_string());
    }

    let parts: Vec<&str> = input.splitn(3, ' ').collect();
    let cmd = parts[0].to_lowercase();

    match cmd.as_str() {
        "format" => {
            if parts.len() < 2 {
                return Err("Usage: format <diskname>".to_string());
            }
            Ok(Command::Format {
                diskname: parts[1].to_string(),
            })
        }
        "mount" => {
            if parts.len() < 2 {
                return Err("Usage: mount <diskname>".to_string());
            }
            Ok(Command::Mount {
                diskname: parts[1].to_string(),
            })
        }
        "umount" => Ok(Command::Umount),
        "register" => {
            if parts.len() < 3 {
                return Err("Usage: register <username> <password>".to_string());
            }
            Ok(Command::Register {
                username: parts[1].to_string(),
                password: parts[2].to_string(),
            })
        }
        "login" => {
            if parts.len() < 3 {
                return Err("Usage: login <username> <password>".to_string());
            }
            Ok(Command::Login {
                username: parts[1].to_string(),
                password: parts[2].to_string(),
            })
        }
        "logout" => Ok(Command::Logout),
        "mkdir" => {
            if parts.len() < 2 {
                return Err("Usage: mkdir <dirname>".to_string());
            }
            Ok(Command::Mkdir {
                dirname: parts[1].to_string(),
            })
        }
        "cd" => {
            if parts.len() < 2 {
                return Err("Usage: cd <dirname>".to_string());
            }
            Ok(Command::Cd {
                dirname: parts[1].to_string(),
            })
        }
        "ls" | "list" | "dir" => Ok(Command::List),
        "rmdir" => {
            if parts.len() < 2 {
                return Err("Usage: rmdir <dirname>".to_string());
            }
            Ok(Command::Rmdir {
                dirname: parts[1].to_string(),
            })
        }
        "create" | "touch" => {
            if parts.len() < 2 {
                return Err("Usage: create <filename>".to_string());
            }
            Ok(Command::Create {
                filename: parts[1].to_string(),
            })
        }
        "delete" | "rm" => {
            if parts.len() < 2 {
                return Err("Usage: delete <filename>".to_string());
            }
            Ok(Command::Delete {
                filename: parts[1].to_string(),
            })
        }
        "read" | "cat" => {
            if parts.len() < 2 {
                return Err("Usage: read <filename>".to_string());
            }
            Ok(Command::Read {
                filename: parts[1].to_string(),
            })
        }
        "write" => {
            if parts.len() < 3 {
                return Err("Usage: write <filename> <data>".to_string());
            }
            let data = parts[2..].join(" ");
            let data = if data.starts_with('"') && data.ends_with('"') {
                data[1..data.len() - 1].to_string()
            } else {
                data
            };
            Ok(Command::Write {
                filename: parts[1].to_string(),
                data,
            })
        }
        "help" => Ok(Command::Help),
        "clear" | "cls" => Ok(Command::Clear),
        "quit" | "exit" => Ok(Command::Quit),
        _ => Err(format!("Unknown command: {}", cmd)),
    }
}

pub fn execute_command(
    cmd: &Command,
    session: &mut Session,
    disk: &mut Option<Disk>,
) -> Result<(Vec<String>, DiskState), String> {
    let mut output = Vec::new();
    let mut disk_state = DiskState::default();

    match cmd {
        Command::Format { diskname } => {
            let mut d = Disk::new(diskname)?;
            format_filesystem(&mut d)?;
            output.push(format!(
                "✓ Filesystem '{}' formatted successfully ({} blocks, {} bytes/block)",
                diskname, d.num_blocks, d.block_size
            ));
            disk_state = DiskState::from_disk(&mut d);
            *disk = Some(d);
        }
        Command::Mount { diskname } => {
            let mut d = Disk::new(diskname)?;
            mount_filesystem(session, &mut d)?;
            output.push(format!("✓ Filesystem '{}' mounted", diskname));
            disk_state = DiskState::from_disk(&mut d);
            *disk = Some(d);
        }
        Command::Umount => {
            umount_filesystem(session);
            output.push("✓ Filesystem unmounted".to_string());
        }
        Command::Register { username, password } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            user_register(d, username, password)?;
            output.push(format!("✓ User '{}' registered successfully", username));
            disk_state = DiskState::from_disk(d);
        }
        Command::Login { username, password } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            user_login(session, d, username, password)?;
            output.push(format!("✓ Logged in as '{}'", username));
            output.push(format!("  Current path: {}", session.current_path));
            disk_state = DiskState::from_disk(d);
        }
        Command::Logout => {
            user_logout(session);
            output.push("✓ Logged out".to_string());
        }
        Command::Mkdir { dirname } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            create_directory(session, d, dirname)?;
            output.push(format!("✓ Directory '{}' created", dirname));
            disk_state = DiskState::from_disk(d);
        }
        Command::Cd { dirname } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            change_directory(session, d, dirname)?;
            output.push(format!("  Current path: {}", session.current_path));
            disk_state = DiskState::from_disk(d);
        }
        Command::List => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            let entries = list_directory(session, d)?;
            if entries.is_empty() {
                output.push("  (empty)".to_string());
            } else {
                output.push(format!("{:28} {:6} {:>8}", "Name", "Type", "Size"));
                output.push("-".repeat(44));
                for (name, type_, size) in &entries {
                    output.push(format!("{:28} {:6} {:>8}", name, type_, size));
                }
            }
            disk_state = DiskState::from_disk(d);
        }
        Command::Rmdir { dirname } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            delete_directory(session, d, dirname)?;
            output.push(format!("✓ Directory '{}' removed", dirname));
            disk_state = DiskState::from_disk(d);
        }
        Command::Create { filename } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            create_file(session, d, filename)?;
            output.push(format!("✓ File '{}' created", filename));
            disk_state = DiskState::from_disk(d);
        }
        Command::Delete { filename } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            delete_file(session, d, filename)?;
            output.push(format!("✓ File '{}' deleted", filename));
            disk_state = DiskState::from_disk(d);
        }
        Command::Read { filename } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            let data = read_file(session, d, filename)?;
            let text = String::from_utf8_lossy(&data);
            output.push(format!("📄 {} [{} bytes]:", filename, data.len()));
            output.push(text.to_string());
            disk_state = DiskState::from_disk(d);
        }
        Command::Write { filename, data } => {
            let d = disk.as_mut().ok_or("No disk mounted")?;
            write_file(session, d, filename, data.as_bytes())?;
            output.push(format!("✓ Written {} bytes to '{}'", data.len(), filename));
            disk_state = DiskState::from_disk(d);
        }
        Command::Help => {
            output.push("Available commands:".to_string());
            output.push(format!("  {:28} {}", "format <diskname>", "Format a new filesystem"));
            output.push(format!("  {:28} {}", "mount <diskname>", "Mount an existing filesystem"));
            output.push(format!("  {:28} {}", "umount", "Unmount filesystem"));
            output.push(format!("  {:28} {}", "register <user> <pass>", "Register a new user"));
            output.push(format!("  {:28} {}", "login <user> <pass>", "Login"));
            output.push(format!("  {:28} {}", "logout", "Logout"));
            output.push(format!("  {:28} {}", "mkdir <dir>", "Create directory"));
            output.push(format!("  {:28} {}", "cd <dir>", "Change directory"));
            output.push(format!("  {:28} {}", "ls", "List directory contents"));
            output.push(format!("  {:28} {}", "rmdir <dir>", "Remove directory"));
            output.push(format!("  {:28} {}", "create <file>", "Create file"));
            output.push(format!("  {:28} {}", "delete <file>", "Delete file"));
            output.push(format!("  {:28} {}", "read <file>", "Read file contents"));
            output.push(format!("  {:28} {}", "write <file> <data>", "Write data to file"));
            output.push(format!("  {:28} {}", "clear / cls", "Clear terminal screen"));
            output.push(format!("  {:28} {}", "help", "Show this help"));
            output.push(format!("  {:28} {}", "quit", "Exit program"));
        }
        Command::Clear => {
            // Handled in app.rs - clear output_lines
        }
        Command::Quit => {
            output.push("Goodbye!".to_string());
        }
    }

    Ok((output, disk_state))
}
