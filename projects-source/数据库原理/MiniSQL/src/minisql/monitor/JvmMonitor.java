package minisql.monitor;

import java.lang.management.*;

public class JvmMonitor {

    public static String getStats(int queryCount) {
        Runtime runtime = Runtime.getRuntime();
        long usedMem = runtime.totalMemory() - runtime.freeMemory();
        long maxMem = runtime.maxMemory();

        ThreadMXBean threadBean = ManagementFactory.getThreadMXBean();
        int threadCount = threadBean.getThreadCount();

        GarbageCollectorMXBean gcBean = null;
        for (GarbageCollectorMXBean g : ManagementFactory.getGarbageCollectorMXBeans()) {
            if (g.getName().contains("Mark Sweep") || g.getName().contains("G1") || g.getName().contains("GC") || g.getName().contains("Young")) {
                gcBean = g; break;
            }
        }

        long gcCount = gcBean != null ? gcBean.getCollectionCount() : -1;
        long gcTime = gcBean != null ? gcBean.getCollectionTime() : -1;
        long uptimeMs = ManagementFactory.getRuntimeMXBean().getUptime();

        StringBuilder sb = new StringBuilder();
        sb.append("┌─ JVM Monitor ──────────────────────────────────┐\n");

        int barLen = 20;
        int filled = (int) (barLen * usedMem / Math.max(maxMem, 1));
        sb.append("│ Heap  ");
        for (int i = 0; i < barLen; i++) sb.append(i < filled ? '█' : '░');
        sb.append(String.format("  %5.1f / %d MB  │%n", usedMem / 1048576.0, maxMem / 1048576));

        sb.append(String.format("│ Threads  %-8d  Queries  %-5d            │%n", threadCount, queryCount));

        if (gcCount >= 0) {
            sb.append(String.format("│ GC Runs  %-8d                        │%n", gcCount));
        }

        long totalSec = uptimeMs / 1000;
        int h = (int) (totalSec / 3600);
        int m = (int) ((totalSec % 3600) / 60);
        int s = (int) (totalSec % 60);
        sb.append(String.format("│ Uptime   %02d:%02d:%02d                              │%n", h, m, s));

        sb.append("└────────────────────────────────────────────────┘");
        return sb.toString();
    }
}
