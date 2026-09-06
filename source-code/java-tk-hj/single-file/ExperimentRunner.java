import java.nio.file.*;
import java.io.*;
import java.util.*;

/** Reproducible single-process benchmark harness for TKHJOPF.java (Java 21). */
public final class ExperimentRunner {
    static final TKHJOPF.Mode[] MODES={TKHJOPF.Mode.NO_BOUNDS,TKHJOPF.Mode.PDUB_ONLY,TKHJOPF.Mode.DUB_ONLY,TKHJOPF.Mode.FULL};
    public static void main(String[] a) throws Exception {
        if(a.length<4){
            System.err.println("Usage: java ExperimentRunner series.txt out.csv warmups repeats");
            System.exit(2);
        }
        Path data=Path.of(a[0]), out=Path.of(a[1]);
        int warmups=Integer.parseInt(a[2]), repeats=Integer.parseInt(a[3]);
        double[] t=TKHJOPF.readSeries(data); int n=t.length;
        int[] Ks={10,50,100,500}; int[] Ls={8,12,16}; double[] mult={0.25,0.5,1,2,4};
        try(PrintWriter pw=new PrintWriter(Files.newBufferedWriter(out))){
            pw.println("dataset,mode,k,topk,minlen,maxlen,rep,runtime_ms,pair_attempts,compatible_pairs,pdub_prunes,dub_prunes,aligned_checks,heap_used_bytes");
            for(int K:Ks) for(int L:Ls){
                if(L>n) continue;
                runCell(pw,data.getFileName().toString(),t,1.0/n,K,2,L,warmups,repeats);
            }
            // forgetting sensitivity uses the central K and max length.
            if(n>=12) for(double c:mult) runCell(pw,data.getFileName().toString(),t,c/n,50,2,12,warmups,repeats);
        }
    }
    static void runCell(PrintWriter pw,String ds,double[] t,double k,int K,int lmin,int lmax,int warmups,int reps){
        for(TKHJOPF.Mode mode:MODES){
            for(int r=-warmups;r<reps;r++){
                TKHJOPF alg=new TKHJOPF(t,k,K,lmin,lmax,mode);
                long t0=System.nanoTime(); alg.mine(); long t1=System.nanoTime();
                if(r<0) continue;
                Runtime rt=Runtime.getRuntime(); long heap=rt.totalMemory()-rt.freeMemory();
                TKHJOPF.Counters c=alg.ctr;
                pw.printf(Locale.ROOT,"%s,%s,%.17g,%d,%d,%d,%d,%.6f,%d,%d,%d,%d,%d,%d%n",
                        ds,mode,k,K,lmin,lmax,r,(t1-t0)/1e6,c.pairAttempts,c.compatiblePairs,
                        c.pdubPrunes,c.dubPrunes,c.alignedComparisons,heap);
                pw.flush();
            }
        }
    }
}
