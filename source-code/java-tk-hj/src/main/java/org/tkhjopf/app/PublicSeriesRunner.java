package org.tkhjopf.app;

import org.tkhjopf.io.TimeSeriesIO;
import org.tkhjopf.miner.MiningResult;
import java.nio.file.*;
import java.io.*;
import java.util.*;

/** One-file public-series timing: same JVM, nanoTime around mine() only. */
public final class PublicSeriesRunner {
    static final String[] MODES = {"hjtopk", "tk-no-pdub", "tk"};

    public static void main(String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("Usage: PublicSeriesRunner input.txt out.csv [warmups] [repeats]");
            System.exit(2);
        }
        Path input = Path.of(args[0]).toAbsolutePath();
        Path out = Path.of(args[1]).toAbsolutePath();
        int warm = args.length > 2 ? Integer.parseInt(args[2]) : 5;
        int rep = args.length > 3 ? Integer.parseInt(args[3]) : 10;
        double[] t = TimeSeriesIO.read(input);
        double k = 1.0 / t.length;
        Files.createDirectories(out.getParent());
        try (PrintWriter tw = new PrintWriter(Files.newBufferedWriter(out))) {
            tw.println("phase,dataset,n,mode,k,topk,minlen,maxlen,rep,runtime_ms,patterns,pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,peak_heap_mb");
            String name = input.getFileName().toString();
            for (String mode : MODES) {
                System.err.println("[public] " + name + " n=" + t.length + " " + mode);
                for (int r = -warm; r < rep; r++) {
                    MiningResult x = CampaignRunner.run(mode, t, k, 50, 2, 12);
                    if (r < 0) continue;
                    var z = x.metrics();
                    tw.printf(Locale.ROOT, "%s,%s,%d,%s,%.17g,%d,%d,%d,%d,%.6f,%d,%d,%d,%d,%d,%d,%.3f%n",
                            "public", name, t.length, mode, k, 50, 2, 12, r,
                            z.runtimeNanos / 1e6, x.patterns().size(), z.pairAttempts, z.compatiblePairs,
                            z.pairDescendantPrunes, z.branchBoundPrunes, z.alignedOccurrenceChecks,
                            z.approxPeakHeapBytes / 1048576.0);
                    tw.flush();
                }
            }
        }
        System.err.println("WROTE " + out);
    }
}
