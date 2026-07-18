use eframe::egui;

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1050.0, 780.0])
            .with_min_inner_size([700.0, 550.0])
            .with_title("二级文件系统仿真 — Rust + egui"),
        ..Default::default()
    };

    eframe::run_native(
        "filesystem-sim",
        options,
        Box::new(|cc| {
            // 运行时加载中文字体（避免编译期嵌入20MB+字体文件）
            let mut fonts = egui::FontDefinitions::default();
            if let Ok(font_data) = std::fs::read("C:/Windows/Fonts/msyh.ttc") {
                fonts.font_data.insert(
                    "microsoft-yahei".to_string(),
                    egui::FontData::from_owned(font_data).into(),
                );
                fonts
                    .families
                    .entry(egui::FontFamily::Proportional)
                    .or_default()
                    .insert(0, "microsoft-yahei".to_string());
                fonts
                    .families
                    .entry(egui::FontFamily::Monospace)
                    .or_default()
                    .push("microsoft-yahei".to_string());
            }
            cc.egui_ctx.set_fonts(fonts);

            Ok(Box::new(filesystem_sim::app::FileSystemApp::default()))
        }),
    )
}
