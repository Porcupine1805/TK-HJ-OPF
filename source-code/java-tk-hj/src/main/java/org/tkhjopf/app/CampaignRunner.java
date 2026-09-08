package org.tkhjopf.app;

import org.tkhjopf.io.TimeSeriesIO;
import org.tkhjopf.miner.*;
import org.tkhjopf.model.ScoredPattern;
import java.nio.file.*;
import java.security.MessageDigest;
import java.io.*;
import java.util.*;

/**
 * Locked campaign for the TK-HJ-OPF manuscript. One JVM, nanoTime around mine() only.
 * Canonical dumps are produced in a separate untimed pass.
 */
public final class CampaignRunner {
    static final String[] MODES = {"hjtopk", "tk-no-bounds", "tk-no-pdub", "tk-no-dub", "tk"};
    static final String[] OFFICIAL = {
        "DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt", "DB4_SP500.txt",
        "DB5_NYSE.txt", "DB6_CL_US.txt", "DB7_HPQ_US.txt", "DB8_GE_US.txt"
    };

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: CampaignRunner dataDir outDir [warmups] [repeats]");
            System.exit(2);
        }
        Path dataDir = Path.of(args[0]).toAbsolutePath();
        Path outDir = Path.of(args[1]).toAbsolutePath();
        int warm = args.length > 2 ? Integer.parseInt(args[2]) : 5;
        int rep = args.length > 3 ? Integer.parseInt(args[3]) : 10;
        Files.createDirectories(outDir);
        Path timing = outDir.resolve("timing.csv");
        Path canonical = outDir.resolve("canonical.csv");
        Path env = outDir.resolve("environment.txt");
        try (PrintWriter ew = new PrintWriter(Files.newBufferedWriter(env))) {
            ew.println("java.version=" + System.getProperty("java.version"));
            ew.println("java.vendor=" + System.getProperty("java.vendor"));
            ew.println("os.name=" + System.getProperty("os.name"));
            ew.println("os.arch=" + System.getProperty("os.arch"));
            ew.println("availableProcessors=" + Runtime.getRuntime().availableProcessors());
            ew.println("maxMemoryMB=" + (Runtime.getRuntime().maxMemory() / 1048576));
            ew.println("warmups=" + warm);
            ew.println("repeats=" + rep);
            ew.println("protocol=in-process; System.nanoTime around mine(); canonical untimed");
        }
        try (PrintWriter tw = new PrintWriter(Files.newBufferedWriter(timing));
             PrintWriter cw = new PrintWriter(Files.newBufferedWriter(canonical))) {
            tw.println("phase,dataset,n,mode,k,topk,minlen,maxlen,rep,runtime_ms,patterns,pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,peak_heap_mb");
            cw.println("dataset,n,mode,k,topk,minlen,maxlen,rank,pattern,support,sha256_cell");
            // Phase 1: canonical exactness at central config
            for (String name : OFFICIAL) {
                Path f = dataDir.resolve(name);
                if (!Files.exists(f)) continue;
                double[] t = TimeSeriesIO.read(f);
                double k = 1.0 / t.length;
                for (String mode : MODES) {
                    MiningResult r = run(mode, t, k, 50, 2, 12);
                    String cell = dumpCanonical(cw, name, t.length, mode, k, 50, 2, 12, r);
                    System.err.println("[canonical] " + name + " " + mode + " sha=" + cell.substring(0, 12) + " patterns=" + r.patterns().size());
                }
            }
            // Phase 2: central timing K=50, L=12
            for (String name : OFFICIAL) {
                Path f = dataDir.resolve(name);
                if (!Files.exists(f)) continue;
                double[] t = TimeSeriesIO.read(f);
                double k = 1.0 / t.length;
                timeGrid(tw, "central", name, t, k, new int[]{50}, new int[]{12}, warm, rep);
            }
            // Phase 3: K sensitivity on DB1-DB3, L=12
            for (String name : new String[]{"DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt"}) {
                Path f = dataDir.resolve(name);
                if (!Files.exists(f)) continue;
                double[] t = TimeSeriesIO.read(f);
                double k = 1.0 / t.length;
                timeGrid(tw, "K_sens", name, t, k, new int[]{10, 50, 100, 500}, new int[]{12}, Math.min(3, warm), Math.min(5, rep));
            }
            // Phase 4: length sensitivity DB1, K=50
            {
                Path f = dataDir.resolve("DB1_Amazon.txt");
                if (Files.exists(f)) {
                    double[] t = TimeSeriesIO.read(f);
                    timeGrid(tw, "L_sens", "DB1_Amazon.txt", t, 1.0 / t.length, new int[]{50}, new int[]{8, 12, 16}, Math.min(3, warm), Math.min(5, rep));
                }
            }
            // Phase 5: forgetting sensitivity DB1 and DB8
            for (String name : new String[]{"DB1_Amazon.txt", "DB8_GE_US.txt"}) {
                Path f = dataDir.resolve(name);
                if (!Files.exists(f)) continue;
                double[] t = TimeSeriesIO.read(f);
                for (double c : new double[]{0.25, 0.5, 1.0, 2.0, 4.0}) {
                    timeGrid(tw, "k_sens", name, t, c / t.length, new int[]{50}, new int[]{12}, Math.min(3, warm), Math.min(5, rep));
                }
            }
        }
        System.err.println("WROTE " + timing);
        System.err.println("WROTE " + canonical);
    }

    static void timeGrid(PrintWriter tw, String phase, String name, double[] t, double k,
                         int[] Ks, int[] Ls, int warm, int rep) {
        for (int K : Ks) for (int L : Ls) {
            if (L > t.length) continue;
            for (String mode : MODES) {
                System.err.println("[" + phase + "] " + name + " n=" + t.length + " " + mode + " K=" + K + " L=" + L);
                for (int r = -warm; r < rep; r++) {
                    MiningResult x = run(mode, t, k, K, 2, L);
                    if (r < 0) continue;
                    var z = x.metrics();
                    tw.printf(Locale.ROOT, "%s,%s,%d,%s,%.17g,%d,%d,%d,%d,%.6f,%d,%d,%d,%d,%d,%d,%.3f%n",
                            phase, name, t.length, mode, k, K, 2, L, r,
                            z.runtimeNanos / 1e6, x.patterns().size(), z.pairAttempts, z.compatiblePairs,
                            z.pairDescendantPrunes, z.branchBoundPrunes, z.alignedOccurrenceChecks,
                            z.approxPeakHeapBytes / 1048576.0);
                    tw.flush();
                }
            }
        }
    }

    static String dumpCanonical(PrintWriter cw, String name, int n, String mode, double k,
                                int K, int minLen, int maxLen, MiningResult r) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        StringBuilder raw = new StringBuilder();
        List<String> rows = new ArrayList<>();
        int rank = 1;
        for (ScoredPattern p : r.patterns()) {
            raw.append(p.pattern().compact()).append('\t')
                    .append(String.format(Locale.ROOT, "%.12f", p.support())).append('\n');
            rows.add(String.format(Locale.ROOT, "%s,%d,%s,%.17g,%d,%d,%d,%d,%s,%.12f",
                    name, n, mode, k, K, minLen, maxLen, rank, p.pattern().compact(), p.support()));
            rank++;
        }
        md.update(raw.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        byte[] dig = md.digest();
        StringBuilder hex = new StringBuilder();
        for (byte b : dig) hex.append(String.format("%02x", b));
        String sha = hex.toString();
        for (String row : rows) cw.println(row + "," + sha);
        cw.flush();
        return sha;
    }

    static MiningResult run(String m, double[] t, double k, int K, int minLen, int max) {
        return switch (m) {
            case "hjtopk" -> new ExhaustiveHJTopKMiner().mine(t, k, K, minLen, max);
            case "tk" -> new TKHJOPFMiner().mine(t, k, K, minLen, max, true, true, true);
            case "tk-naive" -> new TKHJOPFMiner().mine(t, k, K, minLen, max, true, true, false);
            case "tk-no-pdub" -> new TKHJOPFMiner().mine(t, k, K, minLen, max, false, true, true);
            case "tk-no-dub" -> new TKHJOPFMiner().mine(t, k, K, minLen, max, true, false, true);
            case "tk-no-bounds" -> new TKHJOPFMiner().mine(t, k, K, minLen, max, false, false, true);
            default -> throw new IllegalArgumentException(m);
        };
    }
}
