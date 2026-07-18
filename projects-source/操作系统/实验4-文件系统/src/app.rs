use eframe::egui;
use egui::{Color32, Rounding, Stroke, Margin, Frame, Vec2};
use crate::disk::Disk;
use crate::fs::Session;
use crate::shell::{parse_command, execute_command, Command};
use crate::visual::{DiskState, BlockStatus};

pub struct FileSystemApp {
    pub session: Session,
    pub disk: Option<Disk>,
    pub disk_state: DiskState,
    pub output_lines: Vec<(String, Color32)>,
    pub input_buffer: String,
    pub selected_block: Option<usize>,
    pub show_section_labels: bool,
}

impl Default for FileSystemApp {
    fn default() -> Self {
        Self {
            session: Session::new(),
            disk: None,
            disk_state: DiskState::default(),
            output_lines: vec![
                ("💾 二级文件系统仿真  —  Rust + egui".to_string(), Color32::from_rgb(86, 156, 214)),
                ("=".repeat(48).to_string(), Color32::from_rgb(60, 60, 60)),
                ("输入 help 查看可用命令，format <文件名> 开始使用".to_string(), Color32::from_rgb(128, 128, 128)),
            ],
            input_buffer: String::new(),
            selected_block: None,
            show_section_labels: true,
        }
    }
}

impl FileSystemApp {
    pub fn push_output(&mut self, text: &str, color: Color32) {
        for line in text.lines() {
            self.output_lines.push((line.to_string(), color));
        }
        if self.output_lines.len() > 500 {
            self.output_lines.drain(0..100);
        }
    }

    pub fn execute_current_command(&mut self) {
        let input = self.input_buffer.trim().to_string();
        if input.is_empty() { return; }
        self.input_buffer.clear();
        self.push_output(&format!("> {}", input), Color32::from_rgb(86, 156, 214));

        match parse_command(&input) {
            Ok(cmd) => {
                if matches!(cmd, Command::Quit) {
                    self.push_output("Goodbye!", Color32::from_rgb(106, 153, 85));
                    std::process::exit(0);
                }
                if matches!(cmd, Command::Clear) {
                    self.output_lines.clear();
                    self.push_output("💾 二级文件系统仿真  —  Rust + egui", Color32::from_rgb(86, 156, 214));
                    self.push_output(&"=".repeat(48), Color32::from_rgb(60, 60, 60));
                    return;
                }
                match execute_command(&cmd, &mut self.session, &mut self.disk) {
                    Ok((lines, new_state)) => {
                        self.disk_state = new_state;
                        for line in &lines {
                            let color = if line.starts_with('✓') {
                                Color32::from_rgb(106, 153, 85)
                            } else if line.starts_with("✗") || line.starts_with("Error") {
                                Color32::from_rgb(206, 145, 120)
                            } else {
                                Color32::from_rgb(220, 220, 220)
                            };
                            self.push_output(line, color);
                        }
                    }
                    Err(e) => {
                        self.push_output(&format!("✗ {}", e), Color32::from_rgb(206, 145, 120));
                    }
                }
            }
            Err(e) => {
                self.push_output(&format!("✗ {}", e), Color32::from_rgb(206, 145, 120));
            }
        }
    }
}

impl eframe::App for FileSystemApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        ctx.request_repaint();
        ctx.set_visuals(egui::Visuals::dark());

        // ── TOP BAR ──────────────────────────────────────────
        egui::TopBottomPanel::top("top_bar")
            .frame(Frame {
                fill: Color32::from_rgb(25, 25, 25),
                inner_margin: Margin::symmetric(12.0, 8.0),
                ..Default::default()
            })
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    ui.heading(
                        egui::RichText::new("📁 二级文件系统仿真")
                            .size(18.0)
                            .color(Color32::from_rgb(220, 220, 220))
                    );
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        let status = if self.session.mounted {
                            if self.session.logged_in {
                                format!("🔓 {} @ {}", self.session.current_user, self.session.current_path)
                            } else {
                                "🔒 已挂载（未登录）".to_string()
                            }
                        } else {
                            "⛔ 未挂载文件系统".to_string()
                        };
                        let status_color = if self.session.mounted {
                            if self.session.logged_in {
                                Color32::from_rgb(106, 153, 85)
                            } else {
                                Color32::from_rgb(220, 220, 170)
                            }
                        } else {
                            Color32::from_rgb(180, 80, 60)
                        };
                        ui.label(egui::RichText::new(status).size(13.0).color(status_color));
                    });
                });
            });

        // ── LEFT PANEL: Directory Tree ──────────────────────
        egui::SidePanel::left("tree_panel")
            .resizable(true)
            .default_width(220.0)
            .min_width(160.0)
            .frame(Frame {
                fill: Color32::from_rgb(30, 30, 30),
                inner_margin: Margin::symmetric(10.0, 10.0),
                ..Default::default()
            })
            .show(ctx, |ui| {
                // Title
                ui.label(egui::RichText::new("📂 目录树").size(14.0).strong().color(Color32::from_rgb(200, 200, 200)));
                ui.add_space(4.0);
                ui.separator();
                ui.add_space(6.0);

                if self.disk.is_none() {
                    ui.add_space(20.0);
                    ui.label(egui::RichText::new("⛔ 未挂载文件系统")
                        .color(Color32::from_rgb(100, 100, 100))
                        .size(12.0));
                    return;
                }

                let disk = self.disk.as_mut().unwrap();
                // Root
                ui.label(egui::RichText::new("📁 /").color(Color32::from_rgb(220, 220, 170)).size(13.0));
                ui.add_space(4.0);

                match crate::fs::mfd_read(disk) {
                    Ok(mfd) => {
                        for i in 0..mfd.user_count as usize {
                            let user = &mfd.users[i];
                            let name = user.name_str();
                            let is_current = name == self.session.current_user;

                            let (bg_color, text_color) = if is_current {
                                (Color32::from_rgba_premultiplied(60, 50, 20, 80),
                                 Color32::from_rgb(255, 200, 100))
                            } else {
                                (Color32::TRANSPARENT,
                                 Color32::from_rgb(160, 160, 160))
                            };

                            let indent = 8.0;
                            let _resp = Frame {
                                fill: bg_color,
                                rounding: Rounding::same(4.0),
                                inner_margin: Margin::symmetric(6.0, 3.0),
                                ..Default::default()
                            }.show(ui, |ui| {
                                ui.set_min_width(ui.available_width() - indent);
                                let icon = if is_current { "▶ 👤" } else { "  👤" };
                                ui.label(egui::RichText::new(format!("{}{}", icon, name))
                                    .color(text_color).size(13.0));
                            });

                            if is_current {
                                if let Ok(entries) = crate::fs::ufd_read(disk, i) {
                                    ui.add_space(2.0);
                                    for e in entries.iter() {
                                        if !e.is_empty() {
                                            let icon = if e.type_ == 0 { "  📁" } else { "  📄" };
                                            let info = if e.type_ == 1 {
                                                format!(" ({}B)", e.size)
                                            } else {
                                                String::new()
                                            };
                                            ui.label(egui::RichText::new(
                                                format!("{}{}{}", icon, e.name_str(), info))
                                                .color(Color32::from_rgb(140, 180, 140))
                                                .size(12.0));
                                        }
                                    }
                                }
                            }
                            ui.add_space(2.0);
                        }
                    }
                    Err(e) => {
                        ui.label(egui::RichText::new(format!("Error: {}", e))
                            .color(Color32::from_rgb(206, 145, 120)).size(12.0));
                    }
                }
            });

        // ── CENTER: Terminal + Block Detail ──────────────────
        egui::CentralPanel::default()
            .frame(Frame {
                fill: Color32::from_rgb(20, 20, 20),
                inner_margin: Margin::symmetric(8.0, 8.0),
                ..Default::default()
            })
            .show(ctx, |ui| {
                // ── Block Detail (collapsible thin bar) ──
                if self.selected_block.is_some() {
                    Frame {
                        fill: Color32::from_rgb(35, 35, 45),
                        rounding: Rounding::same(4.0),
                        inner_margin: Margin::symmetric(10.0, 6.0),
                        ..Default::default()
                    }.show(ui, |ui| {
                        ui.horizontal(|ui| {
                            ui.label(egui::RichText::new("📋").size(14.0));
                            if let Some(block) = self.selected_block {
                                if block < self.disk_state.blocks.len() {
                                    let info = &self.disk_state.blocks[block];
                                    ui.label(egui::RichText::new(
                                        format!("块 {:3}  │ {:?}  │ {}", block, info.status, info.label))
                                        .color(Color32::from_rgb(180, 180, 200)).size(12.0));
                                }
                            }
                            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                                if ui.button("✕").clicked() {
                                    self.selected_block = None;
                                }
                            });
                        });
                    });
                    ui.add_space(4.0);
                }

                // ── Terminal Window ──
                Frame {
                    fill: Color32::from_rgb(18, 18, 18),
                    rounding: Rounding::same(6.0),
                    stroke: Stroke::new(1.0, Color32::from_rgb(50, 50, 50)),
                    inner_margin: Margin::ZERO,
                    ..Default::default()
                }.show(ui, |ui| {
                    // Terminal title bar
                    Frame {
                        fill: Color32::from_rgb(40, 40, 40),
                        rounding: Rounding::same(6.0),
                        inner_margin: Margin::symmetric(10.0, 5.0),
                        ..Default::default()
                    }.show(ui, |ui| {
                        ui.horizontal(|ui| {
                            // Window dots
                            let dot_color = Color32::from_rgb(80, 80, 80);
                            let dot_size = Vec2::new(8.0, 8.0);
                            let (r, _) = ui.allocate_exact_size(dot_size, egui::Sense::hover());
                            ui.painter().circle_filled(r.center(), 3.5, dot_color);
                            ui.add_space(4.0);
                            let (r, _) = ui.allocate_exact_size(dot_size, egui::Sense::hover());
                            ui.painter().circle_filled(r.center(), 3.5, dot_color);
                            ui.add_space(4.0);
                            let (r, _) = ui.allocate_exact_size(dot_size, egui::Sense::hover());
                            ui.painter().circle_filled(r.center(), 3.5, dot_color);
                            ui.add_space(8.0);
                            ui.label(egui::RichText::new("终端").color(Color32::from_rgb(140, 140, 140)).size(12.0));
                        });
                    });

                    // Terminal output
                    let scroll_h = ui.available_height() - 50.0;
                    egui::ScrollArea::vertical()
                        .id_salt("term_scroll")
                        .max_height(scroll_h.max(40.0))
                        .show(ui, |ui| {
                            ui.add_space(4.0);
                            for (text, color) in &self.output_lines {
                                ui.label(egui::RichText::new(text).color(*color).size(13.0));
                            }
                            ui.scroll_to_cursor(Some(egui::Align::BOTTOM));
                        });

                    // Terminal input bar
                    ui.add_space(2.0);
                    Frame {
                        fill: Color32::from_rgb(25, 25, 25),
                        inner_margin: Margin::symmetric(8.0, 5.0),
                        ..Default::default()
                    }.show(ui, |ui| {
                        ui.horizontal(|ui| {
                            ui.label(egui::RichText::new("$").color(Color32::from_rgb(106, 153, 85)).size(14.0));
                            ui.add_space(4.0);
                            let resp = ui.add_sized(
                                Vec2::new(ui.available_width() - 65.0, 22.0),
                                egui::TextEdit::singleline(&mut self.input_buffer)
                                    .hint_text("输入命令...")
                                    .desired_width(f32::INFINITY)
                                    .font(egui::TextStyle::Monospace),
                            );
                            if ui.button("执行").clicked() {
                                self.execute_current_command();
                            }
                            if resp.lost_focus() && ctx.input(|i| i.key_pressed(egui::Key::Enter)) {
                                self.execute_current_command();
                            }
                            if !resp.has_focus() {
                                resp.request_focus();
                            }
                        });
                    });
                });
            });

        // ── BOTTOM: Disk Block Map ───────────────────────────
        egui::TopBottomPanel::bottom("block_map")
            .resizable(true)
            .default_height(130.0)
            .min_height(80.0)
            .frame(Frame {
                fill: Color32::from_rgb(25, 25, 25),
                inner_margin: Margin::symmetric(12.0, 8.0),
                ..Default::default()
            })
            .show(ctx, |ui| {
                // ── Header row ──
                ui.horizontal(|ui| {
                    ui.label(egui::RichText::new("💾 磁盘块位图").size(14.0).strong().color(Color32::from_rgb(200, 200, 200)));
                    ui.separator();
                    let total = self.disk_state.total_blocks;
                    let used = self.disk_state.used_blocks;
                    let free = self.disk_state.free_blocks;
                    let pct = if total > 0 { used as f32 / total as f32 } else { 0.0 };

                    ui.label(egui::RichText::new(format!("{} 已用 / {} 空闲 / {} 总", used, free, total))
                        .color(Color32::from_rgb(140, 140, 140)).size(11.0));

                    let bar = egui::ProgressBar::new(pct)
                        .desired_width(80.0)
                        .fill(Color32::from_rgb(86, 156, 214));
                    ui.add(bar);

                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        // Legend
                        for (label, color) in [
                            ("引导", Color32::from_rgb(180, 80, 60)),
                            ("Super", Color32::from_rgb(206, 145, 120)),
                            ("MFD", Color32::from_rgb(220, 200, 120)),
                            ("UFD", Color32::from_rgb(200, 180, 100)),
                            ("文件", Color32::from_rgb(86, 156, 214)),
                            ("空闲", Color32::from_rgb(51, 51, 51)),
                        ] {
                            let (r, _) = ui.allocate_exact_size(Vec2::new(8.0, 8.0), egui::Sense::hover());
                            if ui.is_rect_visible(r) {
                                ui.painter().rect_filled(r, Rounding::same(1.0), color);
                            }
                            ui.add_space(2.0);
                            ui.label(egui::RichText::new(label).color(Color32::from_rgb(120, 120, 120)).size(10.0));
                            ui.add_space(6.0);
                        }
                    });
                });
                ui.add_space(4.0);

                // ── Block Grid ──
                let block_size = 16.0;
                let gap = 2.0;
                let blocks_per_row = 24;

                egui::ScrollArea::both()
                    .id_salt("block_grid_scroll")
                    .auto_shrink([false, false])
                    .show(ui, |ui| {
                        let cell_w = block_size + gap;
                        let total_w = blocks_per_row as f32 * cell_w;
                        ui.set_min_width(total_w);

                        for (i, block) in self.disk_state.blocks.iter().enumerate() {
                            if i % blocks_per_row == 0 {
                                if i > 0 { ui.end_row(); }
                                ui.horizontal(|ui| {
                                    ui.set_height(block_size);
                                    // Row label
                                    ui.label(egui::RichText::new(format!("{:3}", i))
                                        .color(Color32::from_rgb(80, 80, 80))
                                        .size(9.0)
                                        .monospace());
                                });
                            }

                            let color = block_color(&block.status);
                            let is_selected = self.selected_block == Some(i);
                            let stroke = if is_selected {
                                Stroke::new(2.0, Color32::WHITE)
                            } else {
                                Stroke::new(0.5, Color32::from_rgb(40, 40, 40))
                            };

                            let (rect, response) = ui.allocate_exact_size(
                                Vec2::new(block_size, block_size),
                                egui::Sense::click(),
                            );

                            if ui.is_rect_visible(rect) {
                                ui.painter().rect_filled(rect, Rounding::same(2.0), color);
                                ui.painter().rect_stroke(rect, Rounding::same(2.0), stroke);
                            }

                            let block_num = i;
                            let st = block.status.clone();
                            let lbl = block.label.clone();
                            let resp2 = response.on_hover_ui(|ui| {
                                ui.label(egui::RichText::new(format!("块 {}", block_num)).strong().size(12.0));
                                ui.label(format!("类型: {:?}", st));
                                ui.label(format!("标签: {}", lbl));
                            });

                            if resp2.clicked() {
                                self.selected_block = if is_selected { None } else { Some(i) };
                            }
                            ui.add_space(gap);
                        }
                        ui.end_row();
                    });
            });
    }
}

fn block_color(status: &BlockStatus) -> Color32 {
    match status {
        BlockStatus::Boot => Color32::from_rgb(180, 80, 60),
        BlockStatus::SuperBlock => Color32::from_rgb(206, 145, 120),
        BlockStatus::MFD => Color32::from_rgb(220, 200, 120),
        BlockStatus::UFD => Color32::from_rgb(200, 180, 100),
        BlockStatus::FileData => Color32::from_rgb(86, 156, 214),
        BlockStatus::Free => Color32::from_rgb(51, 51, 51),
    }
}
