package minisql.repl;

import java.util.List;

public class ResultRenderer {
    private final int termWidth;

    public ResultRenderer() { this.termWidth = 80; }

    public void render(List<String> outputLines, List<String> history) {
        // Output lines are already formatted by Engine - just add to history
        history.addAll(outputLines);
    }

    public static String success(String msg) { return "✓ " + msg; }
    public static String error(String msg) { return "✗ " + msg; }
    public static String info(String msg) { return "  " + msg; }
}
