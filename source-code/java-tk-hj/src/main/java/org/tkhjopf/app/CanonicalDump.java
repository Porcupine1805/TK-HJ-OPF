package org.tkhjopf.app;

import org.tkhjopf.io.TimeSeriesIO;
import org.tkhjopf.miner.MiningResult;
import org.tkhjopf.model.ScoredPattern;
import java.nio.file.*;
import java.security.MessageDigest;
import java.io.*;
import java.util.*;

/** Tab-separated canonical dump (patterns contain commas). */
public final class CanonicalDump {
    static final String[] MODES = {"hjtopk", "tk-no-bounds", "tk-no-pdub", "tk-no-dub", "tk"};
    static final String[] OFFICIAL = {
        "DB1_Amazon.txt", "DB2_Russell2000.txt", "DB3_Nasdaq.txt", "DB4_SP500.txt",
        "DB5_NYSE.txt", "DB6_CL_US.txt", "DB7_HPQ_US.txt", "DB8_GE_US.txt"
    };

    public static void main(String[] args) throws Exception {
        Path dataDir = Path.of(args[0]).toAbsolutePath();
        Path out = Path.of(args[1]).toAbsolutePath();
        Files.createDirectories(out.getParent() == null ? Path.of(".") : out.getParent());
        try (PrintWriter w = new PrintWriter(Files.newBufferedWriter(out))) {
            w.println("dataset\tn\tmode\tk\ttopk\tmaxlen\trank\tpattern\tsupport\tsha256");
            for (String name : OFFICIAL) {
                Path f = dataDir.resolve(name);
                if (!Files.exists(f)) continue;
                double[] t = TimeSeriesIO.read(f);
                double k = 1.0 / t.length;
                Map<String, String> shas = new LinkedHashMap<>();
                for (String mode : MODES) {
                    MiningResult r = CampaignRunner.run(mode, t, k, 50, 2, 12);
                    StringBuilder raw = new StringBuilder();
                    List<String> rows = new ArrayList<>();
                    int rank = 1;
                    for (ScoredPattern p : r.patterns()) {
                        raw.append(p.pattern().compact()).append('\t')
                                .append(String.format(Locale.ROOT, "%.12f", p.support())).append('\n');
                        rows.add(String.format(Locale.ROOT, "%s\t%d\t%s\t%.17g\t%d\t%d\t%d\t%s\t%.12f",
                                name, t.length, mode, k, 50, 12, rank, p.pattern().compact(), p.support()));
                        rank++;
                    }
                    MessageDigest md = MessageDigest.getInstance("SHA-256");
                    md.update(raw.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    StringBuilder hex = new StringBuilder();
                    for (byte b : md.digest()) hex.append(String.format("%02x", b));
                    String sha = hex.toString();
                    shas.put(mode, sha);
                    for (String row : rows) w.println(row + "\t" + sha);
                    System.err.println(name + " " + mode + " " + sha.substring(0, 16) + " npat=" + r.patterns().size());
                }
                long uniq = shas.values().stream().distinct().count();
                System.err.println("AGREE " + name + " unique_sha=" + uniq);
            }
        }
    }
}
