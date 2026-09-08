package org.tkhjopf.app;

import org.tkhjopf.io.TimeSeriesIO;
import org.tkhjopf.miner.MiningResult;

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
 * Central-cell ablation: DUB-only vs naive PDUB vs profile PDUB.
 * Same JVM, nanoTime around mine(); canonical SHA compared per dataset.
 */
public final class ProfileAblationRunner {
    static final String[] MODES = {"tk-no-pdub", "tk-naive", "tk"};
    static final String[] OFFICIAL = {
            "DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt", "DB4_SP500.txt",
            "DB5_NYSE.txt", "DB6_CL_US.txt", "DB7_HPQ_US.txt", "DB8_GE_US.txt"
    };
    static final String[] PUBLIC = {"SILSO_sunspots.txt", "NASDAQCOM.txt", "FRED_SP500.txt"};

    public static void main(String[] args) throws Exception {
        if (args.length < 3) {
            System.err.println("Usage: ProfileAblationRunner officialDir publicDir outDir");
            System.exit(2);
        }
        Path official = Path.of(args[0]).toAbsolutePath();
        Path pubDir = Path.of(args[1]).toAbsolutePath();
        Path outDir = Path.of(args[2]).toAbsolutePath();
        int warm = 5, rep = 10;
        Files.createDirectories(outDir);
        Path timing = outDir.resolve("profile_ablation.csv");
        Path canon = outDir.resolve("profile_ablation_canonical.tsv");
        try (PrintWriter tw = new PrintWriter(Files.newBufferedWriter(timing));
             PrintWriter cw = new PrintWriter(Files.newBufferedWriter(canon))) {
            tw.println("phase,dataset,n,mode,k,topk,minlen,maxlen,rep,runtime_ms,patterns,pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,peak_heap_mb");
            cw.println("dataset\tmode\tsha256\tnpat\taligned\tpdub_prunes\tdub_prunes");
            List<Path> series = new ArrayList<>();
            for (String name : OFFICIAL) {
                Path f = official.resolve(name);
                if (Files.exists(f)) series.add(f);
            }
            for (String name : PUBLIC) {
                Path f = pubDir.resolve(name);
                if (Files.exists(f)) series.add(f);
            }
            for (Path f : series) {
                String name = f.getFileName().toString();
                double[] t = TimeSeriesIO.read(f);
                double k = 1.0 / t.length;
                System.err.println("[load] " + name + " n=" + t.length);
                Map<String, String> shas = new LinkedHashMap<>();
                Map<String, long[]> counters = new LinkedHashMap<>();
                for (String mode : MODES) {
                    MiningResult r = CampaignRunner.run(mode, t, k, 50, 2, 12);
                    String sha = shaOf(r);
                    shas.put(mode, sha);
                    var z = r.metrics();
                    counters.put(mode, new long[]{z.alignedOccurrenceChecks, z.pairDescendantPrunes, z.branchBoundPrunes, r.patterns().size()});
                    cw.printf(Locale.ROOT, "%s\t%s\t%s\t%d\t%d\t%d\t%d%n",
                            name, mode, sha, r.patterns().size(), z.alignedOccurrenceChecks,
                            z.pairDescendantPrunes, z.branchBoundPrunes);
                    cw.flush();
                    System.err.println("[canonical] " + name + " " + mode + " sha=" + sha.substring(0, 16)
                            + " aligned=" + z.alignedOccurrenceChecks + " pdub=" + z.pairDescendantPrunes);
                }
                long uniq = shas.values().stream().distinct().count();
                boolean treeEq = sameTree(counters.get("tk-naive"), counters.get("tk"));
                System.err.println("[agree] " + name + " unique_sha=" + uniq + " profile_vs_naive_tree="
                        + (treeEq ? "IDENTICAL" : "DIFFER"));
                if (uniq != 1) throw new IllegalStateException("canonical mismatch on " + name);
                if (!treeEq) throw new IllegalStateException("search tree mismatch on " + name);
                for (String mode : MODES) {
                    System.err.println("[ablation] " + name + " " + mode);
                    for (int i = -warm; i < rep; i++) {
                        MiningResult x = CampaignRunner.run(mode, t, k, 50, 2, 12);
                        if (i < 0) continue;
                        var z = x.metrics();
                        tw.printf(Locale.ROOT,
                                "%s,%s,%d,%s,%.17g,%d,%d,%d,%d,%.6f,%d,%d,%d,%d,%d,%d,%.3f%n",
                                "ablation", name, t.length, mode, k, 50, 2, 12, i,
                                z.runtimeNanos / 1e6, x.patterns().size(), z.pairAttempts, z.compatiblePairs,
                                z.pairDescendantPrunes, z.branchBoundPrunes, z.alignedOccurrenceChecks,
                                z.approxPeakHeapBytes / 1048576.0);
                        tw.flush();
                    }
                }
            }
        }
        System.err.println("WROTE " + timing);
    }

    static boolean sameTree(long[] a, long[] b) {
        if (a == null || b == null || a.length != b.length) return false;
        for (int i = 0; i < a.length; i++) if (a[i] != b[i]) return false;
        return true;
    }

    static String shaOf(MiningResult r) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        StringBuilder raw = new StringBuilder();
        r.patterns().forEach(p -> raw.append(p.pattern().compact()).append('\t')
                .append(String.format(Locale.ROOT, "%.12f", p.support())).append('\n'));
        md.update(raw.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
        StringBuilder hex = new StringBuilder();
        for (byte v : md.digest()) hex.append(String.format("%02x", v));
        return hex.toString();
    }
}
