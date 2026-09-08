package org.tkhjopf.app;

import org.tkhjopf.io.TimeSeriesIO;
import org.tkhjopf.miner.MiningResult;
import org.tkhjopf.model.ScoredPattern;

import java.io.PrintWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Five-mode canonical + central timing for arbitrary series (one JVM).
 * nanoTime is taken inside mine(); canonical dumps are untimed and written first.
 */
public final class Paper1SeriesRunner {
    static final String[] MODES = {"hjtopk", "tk-no-bounds", "tk-no-pdub", "tk-no-dub", "tk"};

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: Paper1SeriesRunner outDir series.txt [series.txt ...]");
            System.exit(2);
        }
        Path outDir = Path.of(args[0]).toAbsolutePath();
        int warm = 5;
        int rep = 10;
        Files.createDirectories(outDir);
        Path timing = outDir.resolve("full_paper1.csv");
        Path canonical = outDir.resolve("full_paper1_canonical.tsv");
        Path env = outDir.resolve("full_paper1_environment.txt");
        try (PrintWriter ew = new PrintWriter(Files.newBufferedWriter(env))) {
            ew.println("java.version=" + System.getProperty("java.version"));
            ew.println("java.vendor=" + System.getProperty("java.vendor"));
            ew.println("os.name=" + System.getProperty("os.name"));
            ew.println("os.arch=" + System.getProperty("os.arch"));
            ew.println("os.version=" + System.getProperty("os.version"));
            ew.println("availableProcessors=" + Runtime.getRuntime().availableProcessors());
            ew.println("maxMemoryMB=" + (Runtime.getRuntime().maxMemory() / 1048576));
            ew.println("warmups=" + warm);
            ew.println("repeats=" + rep);
            ew.println("K=50");
            ew.println("minLen=2");
            ew.println("maxLen=12");
            ew.println("k=1/n");
            ew.println("protocol=canonical untimed then 5 warmup + 10 measured; nanoTime around mine()");
            ew.println("modes=" + String.join(",", MODES));
        }
        try (PrintWriter tw = new PrintWriter(Files.newBufferedWriter(timing));
             PrintWriter cw = new PrintWriter(Files.newBufferedWriter(canonical))) {
            tw.println("phase,dataset,n,mode,k,topk,minlen,maxlen,rep,runtime_ms,patterns,pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,peak_heap_mb");
            cw.println("dataset\tn\tmode\tk\ttopk\tmaxlen\trank\tpattern\tsupport\tsha256");
            for (int i = 1; i < args.length; i++) {
                Path f = Path.of(args[i]).toAbsolutePath();
                if (!Files.exists(f)) {
                    System.err.println("SKIP missing " + f);
                    continue;
                }
                String name = f.getFileName().toString();
                double[] t = TimeSeriesIO.read(f);
                double k = 1.0 / t.length;
                System.err.println("[load] " + name + " n=" + t.length);
                Map<String, String> shas = new LinkedHashMap<>();
                for (String mode : MODES) {
                    MiningResult r = CampaignRunner.run(mode, t, k, 50, 2, 12);
                    String sha = dumpCanonical(cw, name, t.length, mode, k, 50, 12, r);
                    shas.put(mode, sha);
                    System.err.println("[canonical] " + name + " " + mode
                            + " sha=" + sha.substring(0, 16) + " npat=" + r.patterns().size());
                }
                long uniq = shas.values().stream().distinct().count();
                System.err.println("[agree] " + name + " unique_sha=" + uniq);
                for (String mode : MODES) {
                    System.err.println("[central] " + name + " n=" + t.length + " " + mode);
                    for (int r = -warm; r < rep; r++) {
                        MiningResult x = CampaignRunner.run(mode, t, k, 50, 2, 12);
                        if (r < 0) continue;
                        var z = x.metrics();
                        tw.printf(Locale.ROOT,
                                "%s,%s,%d,%s,%.17g,%d,%d,%d,%d,%.6f,%d,%d,%d,%d,%d,%d,%.3f%n",
                                "public", name, t.length, mode, k, 50, 2, 12, r,
                                z.runtimeNanos / 1e6, x.patterns().size(), z.pairAttempts, z.compatiblePairs,
                                z.pairDescendantPrunes, z.branchBoundPrunes, z.alignedOccurrenceChecks,
                                z.approxPeakHeapBytes / 1048576.0);
                        tw.flush();
                    }
                }
            }
        }
        System.err.println("WROTE " + timing);
        System.err.println("WROTE " + canonical);
    }

    static String dumpCanonical(PrintWriter cw, String name, int n, String mode, double k,
                                int K, int maxLen, MiningResult r) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        StringBuilder raw = new StringBuilder();
        List<String> rows = new ArrayList<>();
        int rank = 1;
        for (ScoredPattern p : r.patterns()) {
            raw.append(p.pattern().compact()).append('\t')
                    .append(String.format(Locale.ROOT, "%.12f", p.support())).append('\n');
            rows.add(String.format(Locale.ROOT, "\t%d\t%s\t%.17g\t%d\t%d\t%d\t%s\t%.12f",
                    n, mode, k, K, maxLen, rank, p.pattern().compact(), p.support()));
            rank++;
        }
        md.update(raw.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        byte[] dig = md.digest();
        StringBuilder hex = new StringBuilder();
        for (byte b : dig) hex.append(String.format("%02x", b));
        String sha = hex.toString();
        for (String row : rows) cw.println(name + row + "\t" + sha);
        cw.flush();
        return sha;
    }
}
