import java.io.*;
import java.nio.file.*;
import java.util.*;

/**
 * Clean-room Java 21 reference implementation for
 * TK-HJ-OPF: exact top-K order-preserving pattern mining under exponential forgetting.
 *
 * Semantics:
 *  - strict rank encoding: windows containing ties are rejected;
 *  - occurrences are stored by 1-based ending position;
 *  - w_j = exp(-k (n-j)); fsup(p) = sum_{j in Occ(p)} w_j;
 *  - deterministic result order: larger fsup, then shorter pattern, then lexicographic ranks.
 *
 * The code intentionally favors auditability.  The experimental manuscript uses the same
 * logical operations: prefix/suffix hash join, immutable occurrence-list fusion, a bounded
 * top-K heap, PDUB before alignment, and DUB after child materialization.
 */
public final class TKHJOPF {
    enum Mode { FULL, DUB_ONLY, PDUB_ONLY, NO_BOUNDS }

    static final class Key {
        final int[] a;
        final int hash;
        Key(int[] x) { this.a = x; this.hash = Arrays.hashCode(x); }
        @Override public int hashCode() { return hash; }
        @Override public boolean equals(Object o) {
            return o instanceof Key k && Arrays.equals(a, k.a);
        }
        @Override public String toString() { return Arrays.toString(a); }
    }

    static final class Pattern {
        final int[] ranks;
        final int[] ends;              // sorted, 1-based ending positions
        final double fsup;
        Key preKey, sufKey;
        Pattern(int[] ranks, int[] ends, double fsup) {
            this.ranks = ranks; this.ends = ends; this.fsup = fsup;
        }
        int length() { return ranks.length; }
        Key key() { return new Key(ranks); }
        @Override public String toString() {
            return Arrays.toString(ranks) + "  Occ=" + Arrays.toString(ends)
                    + "  fsup=" + String.format(Locale.ROOT, "%.9f", fsup);
        }
    }

    static final class IntList {
        int[] a = new int[8]; int size = 0;
        void add(int x) { if (size == a.length) a = Arrays.copyOf(a, a.length * 2); a[size++] = x; }
        int[] toArray() { return Arrays.copyOf(a, size); }
    }

    static final class Counters {
        long pairAttempts, compatiblePairs, pdubPrunes, dubPrunes, alignedComparisons;
        @Override public String toString() {
            return "pairAttempts="+pairAttempts+", compatiblePairs="+compatiblePairs+
                    ", pdubPrunes="+pdubPrunes+", dubPrunes="+dubPrunes+
                    ", alignedComparisons="+alignedComparisons;
        }
    }

    final double[] t;
    final int n;
    final double k;
    final int K, lmin, lmax;
    final Mode mode;
    final double[] w;                  // w[1..n]
    final Counters ctr = new Counters();

    // Positive means x is better than y.  A PriorityQueue using this comparator has the worst root.
    static int qualityCompare(Pattern x, Pattern y) {
        int c = Double.compare(x.fsup, y.fsup);
        if (c != 0) return c;
        c = Integer.compare(y.length(), x.length()); // shorter is better
        if (c != 0) return c;
        return -lexCompare(x.ranks, y.ranks);        // lexicographically smaller is better
    }
    static int lexCompare(int[] a, int[] b) {
        int m = Math.min(a.length, b.length);
        for (int i=0;i<m;i++) if (a[i] != b[i]) return Integer.compare(a[i], b[i]);
        return Integer.compare(a.length, b.length);
    }

    TKHJOPF(double[] t, double k, int K, int lmin, int lmax, Mode mode) {
        if (k <= 0 || K < 1 || lmin < 2 || lmax < lmin || lmax > t.length)
            throw new IllegalArgumentException("Invalid parameters");
        this.t = t; this.n = t.length; this.k = k; this.K = K;
        this.lmin = lmin; this.lmax = lmax; this.mode = mode;
        this.w = new double[n+1];
        for (int j=1;j<=n;j++) w[j] = Math.exp(-k * (n-j));
    }

    List<Pattern> mine() {
        PriorityQueue<Pattern> heap = new PriorityQueue<>(TKHJOPF::qualityCompare);
        Map<Key,Pattern> f2 = buildLength2();
        if (lmin <= 2) for (Pattern p : f2.values()) offer(heap,p);

        Map<Key,Pattern> frontier = new LinkedHashMap<>();
        for (Pattern p : f2.values()) {
            if (!useDUB() || heap.size() < K || !safeLess(dub(p), theta(heap))) frontier.put(p.key(), p);
            else ctr.dubPrunes++;
        }

        for (int m=2; m<lmax && !frontier.isEmpty(); m++) {
            Map<Key,List<Pattern>> index = new HashMap<>();
            for (Pattern q : frontier.values())
                index.computeIfAbsent(preKey(q), z -> new ArrayList<>()).add(q);

            Map<Key,Pattern> next = new LinkedHashMap<>();
            int pairDepth = lmax - (m+1);
            for (Pattern p : frontier.values()) {
                List<Pattern> bucket = index.get(sufKey(p));
                if (bucket == null) continue;
                for (Pattern q : bucket) {
                    ctr.pairAttempts++;
                    ctr.compatiblePairs++;
                    if (usePDUB() && heap.size()==K && safeLess(pdub(p,q,pairDepth), theta(heap))) {
                        ctr.pdubPrunes++;
                        continue;
                    }
                    for (Pattern r : fuse(p,q)) {
                        if (r.length() >= lmin) offer(heap,r);
                        if (r.length() < lmax) {
                            if (!useDUB() || heap.size()<K || !safeLess(dub(r), theta(heap))) next.put(r.key(),r);
                            else ctr.dubPrunes++;
                        }
                    }
                }
            }
            frontier = next;
        }
        ArrayList<Pattern> ans = new ArrayList<>(heap);
        ans.sort((a,b) -> -qualityCompare(a,b));
        return ans;
    }

    boolean useDUB() { return mode == Mode.FULL || mode == Mode.DUB_ONLY; }
    boolean usePDUB() { return mode == Mode.FULL || mode == Mode.PDUB_ONLY; }

    double theta(PriorityQueue<Pattern> h) { return h.size()==K ? h.peek().fsup : 0.0; }
    void offer(PriorityQueue<Pattern> h, Pattern p) {
        if (h.size() < K) h.add(p);
        else if (qualityCompare(p,h.peek()) > 0) { h.poll(); h.add(p); }
    }

    Map<Key,Pattern> buildLength2() {
        Map<Key,IntList> occ = new LinkedHashMap<>();
        for (int j=2;j<=n;j++) {
            double a=t[j-2], b=t[j-1];
            if (a==b) continue;
            int[] r = a<b ? new int[]{1,2} : new int[]{2,1};
            occ.computeIfAbsent(new Key(r),z->new IntList()).add(j);
        }
        Map<Key,Pattern> out = new LinkedHashMap<>();
        for (var e:occ.entrySet()) {
            int[] ends=e.getValue().toArray();
            Pattern p=new Pattern(e.getKey().a,ends,score(ends));
            out.put(p.key(),p);
        }
        return out;
    }

    double score(int[] ends) { double s=0; for(int j:ends) s+=w[j]; return s; }

    static int[] projectRemove(int[] p, int removeIndex) {
        int x=p[removeIndex], m=p.length;
        int[] out=new int[m-1]; int z=0;
        for(int i=0;i<m;i++) if(i!=removeIndex) out[z++]=p[i]-(p[i]>x?1:0);
        return out;
    }
    Key preKey(Pattern p) {
        if (p.preKey==null) p.preKey=new Key(projectRemove(p.ranks,p.ranks.length-1));
        return p.preKey;
    }
    Key sufKey(Pattern p) {
        if (p.sufKey==null) p.sufKey=new Key(projectRemove(p.ranks,0));
        return p.sufKey;
    }

    // Build the unique candidate consistent with p,q and the chosen first-vs-last relation.
    static int[] candidate(int[] p, int[] q, boolean firstLessLast) {
        int m=p.length;
        int[] r=new int[m+1];
        r[0]=p[0]+(firstLessLast?0:1);
        for(int i=1;i<m;i++) r[i]=p[i]+(q[i-1]>q[m-1]?1:0);
        r[m]=q[m-1]+(firstLessLast?1:0);
        if (!isPermutation(r)) return null;
        if (firstLessLast != (r[0]<r[m])) return null;
        if (!Arrays.equals(projectRemove(r,m),p)) return null;
        if (!Arrays.equals(projectRemove(r,0),q)) return null;
        return r;
    }
    static boolean isPermutation(int[] r) {
        boolean[] seen=new boolean[r.length+1];
        for(int x:r) if(x<1||x>r.length||seen[x]) return false; else seen[x]=true;
        return true;
    }

    List<Pattern> fuse(Pattern p, Pattern q) {
        int m=p.length();
        int[] less=candidate(p.ranks,q.ranks,true);
        int[] greater=candidate(p.ranks,q.ranks,false);
        IntList le=new IntList(), ge=new IntList();
        int i=0,j=0;
        while(i<p.ends.length && j<q.ends.length) {
            ctr.alignedComparisons++;
            int pe=p.ends[i]+1, qe=q.ends[j];
            if(pe<qe) { i++; continue; }
            if(pe>qe) { j++; continue; }
            int end=qe; // 1-based
            double first=t[end-(m+1)], last=t[end-1];
            if(first<last && less!=null) le.add(end);
            else if(first>last && greater!=null) ge.add(end);
            i++; j++;
        }
        ArrayList<Pattern> out=new ArrayList<>(2);
        if(less!=null && le.size>0) { int[] e=le.toArray(); out.add(new Pattern(less,e,score(e))); }
        if(greater!=null && ge.size>0) { int[] e=ge.toArray(); out.add(new Pattern(greater,e,score(e))); }
        return out;
    }

    double ub(Pattern p, int d) {
        if(d<0) return Double.POSITIVE_INFINITY;
        int cutoff=n-d;
        int z=upperBound(p.ends,cutoff); // number of endpoints <= cutoff
        double s=0; // D is <=14 in the locked experiments; exact direct sum keeps code auditable.
        for(int i=0;i<z;i++) s+=w[p.ends[i]];
        return Math.exp(k*d)*s;
    }
    static int upperBound(int[] a,int x) {
        int lo=0,hi=a.length;
        while(lo<hi){ int mid=(lo+hi)>>>1; if(a[mid]<=x) lo=mid+1; else hi=mid; }
        return lo;
    }
    double dub(Pattern p) {
        int D=lmax-p.length(); double best=0;
        for(int d=0;d<=D;d++) best=Math.max(best,ub(p,d));
        return best;
    }
    double pdub(Pattern p,Pattern q,int D) {
        double best=0;
        for(int d=0;d<=D;d++) best=Math.max(best,Math.min(ub(p,d+1),ub(q,d)));
        return best;
    }
    static boolean safeLess(double bound,double theta) {
        double scale=Math.max(1.0,Math.max(Math.abs(bound),Math.abs(theta)));
        double eps=Math.max(1e-12,32.0*Math.ulp(scale));
        return bound + eps < theta;
    }

    // Exhaustive semantic oracle for small inputs.
    List<Pattern> bruteForce() {
        Map<Key,IntList> occ=new HashMap<>();
        for(int m=lmin;m<=lmax;m++) for(int end=m;end<=n;end++) {
            double[] z=Arrays.copyOfRange(t,end-m,end);
            int[] r=normalizeStrict(z); if(r==null) continue;
            occ.computeIfAbsent(new Key(r),x->new IntList()).add(end);
        }
        PriorityQueue<Pattern> h=new PriorityQueue<>(TKHJOPF::qualityCompare);
        for(var e:occ.entrySet()){ int[] ends=e.getValue().toArray(); offer(h,new Pattern(e.getKey().a,ends,score(ends))); }
        ArrayList<Pattern> ans=new ArrayList<>(h); ans.sort((a,b)->-qualityCompare(a,b)); return ans;
    }
    static int[] normalizeStrict(double[] z) {
        int m=z.length; int[] r=new int[m];
        for(int i=0;i<m;i++){
            int rank=1;
            for(int h=0;h<m;h++){
                if(i!=h && z[i]==z[h]) return null;
                if(z[h]<z[i]) rank++;
            }
            r[i]=rank;
        }
        return r;
    }

    static boolean sameAnswer(List<Pattern>a,List<Pattern>b,double tol){
        if(a.size()!=b.size())return false;
        for(int i=0;i<a.size();i++){
            if(!Arrays.equals(a.get(i).ranks,b.get(i).ranks))return false;
            if(Math.abs(a.get(i).fsup-b.get(i).fsup)>tol)return false;
        }
        return true;
    }

    static double[] readSeries(Path p) throws IOException {
        String s=Files.readString(p); String[] toks=s.trim().split("[\\s,;]+");
        double[] x=new double[toks.length]; for(int i=0;i<toks.length;i++) x[i]=Double.parseDouble(toks[i]); return x;
    }

    static Mode parseMode(String s){
        return switch(s.toLowerCase(Locale.ROOT)){
            case "full","tk" -> Mode.FULL;
            case "dub-only","tk-no-pdub" -> Mode.DUB_ONLY;
            case "pdub-only","tk-no-dub" -> Mode.PDUB_ONLY;
            case "no-bounds","hjtopk" -> Mode.NO_BOUNDS;
            default -> throw new IllegalArgumentException("mode: full|dub-only|pdub-only|no-bounds");
        };
    }

    public static void main(String[] args) throws Exception {
        if(args.length==0){
            double[] t={15,32,29,27,34,33,25,20,28,23};
            TKHJOPF alg=new TKHJOPF(t,0.1,5,2,10,Mode.FULL);
            List<Pattern> ans=alg.mine(), oracle=alg.bruteForce();
            System.out.println("Unified running example; exact top-5:");
            for(int i=0;i<ans.size();i++) System.out.printf(Locale.ROOT,"%d. %s%n",i+1,ans.get(i));
            System.out.println("Counters: "+alg.ctr);
            System.out.println("Brute-force agreement: "+sameAnswer(ans,oracle,1e-10));
            return;
        }
        if(args.length<6){
            System.err.println("Usage: java TKHJOPF series.txt k K lmin lmax mode");
            System.exit(2);
        }
        double[] t=readSeries(Path.of(args[0]));
        TKHJOPF alg=new TKHJOPF(t,Double.parseDouble(args[1]),Integer.parseInt(args[2]),
                Integer.parseInt(args[3]),Integer.parseInt(args[4]),parseMode(args[5]));
        long t0=System.nanoTime(); List<Pattern> ans=alg.mine(); long t1=System.nanoTime();
        System.out.printf(Locale.ROOT,"runtime_ms=%.6f%n",(t1-t0)/1e6);
        System.out.println(alg.ctr);
        for(int i=0;i<ans.size();i++) System.out.printf(Locale.ROOT,"%d\t%s%n",i+1,ans.get(i));
    }
}
