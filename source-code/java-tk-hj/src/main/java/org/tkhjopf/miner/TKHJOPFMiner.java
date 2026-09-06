package org.tkhjopf.miner;

import org.tkhjopf.core.*;
import org.tkhjopf.model.*;
import org.tkhjopf.metrics.Metrics;
import java.util.*;

public final class TKHJOPFMiner {
    /** Conservative slack is used only in pruning comparisons, never as a non-transitive heap comparator. */
    private static final double PRUNE_EPS=1e-12;

    public MiningResult mine(double[] t,double k,int topK,int maxLen){
        return mine(t,k,topK,2,maxLen,true,true);
    }

    public MiningResult mine(double[] t,double k,int topK,int minLen,int maxLen){
        return mine(t,k,topK,minLen,maxLen,true,true);
    }

    public MiningResult mine(double[] t,double k,int topK,int minLen,int maxLen,boolean usePDUB,boolean useDUB){
        if(topK<=0)throw new IllegalArgumentException("topK must be positive");
        if(minLen<2)throw new IllegalArgumentException("minLen must be >= 2");
        long start=System.nanoTime();Metrics met=new Metrics();double[]w=Forgetting.weights(t.length,k);
        if(maxLen<=0||maxLen>t.length)maxLen=t.length;
        if(minLen>maxLen)throw new IllegalArgumentException("minLen > maxLen");
        PriorityQueue<ScoredPattern> heap=new PriorityQueue<>(topK, TKHJOPFMiner::compareWorstFirst);
        List<PatternData>cur=SeedFactory.length2(t,w);
        if(minLen<=2) for(PatternData p:cur)offer(heap,BaselineOPFMiner.score(p),topK);
        if(useDUB) cur=branchFilter(cur,t.length,k,w,maxLen,heap,topK,met);met.sampleHeap();
        for(int m=2;m<maxLen&&!cur.isEmpty();m++){
            Map<IntArrayKey,List<PatternData>>idx=new HashMap<>();
            for(PatternData q:cur)idx.computeIfAbsent(q.prefix,z->new ArrayList<>()).add(q);
            LinkedHashMap<Pattern,PatternData>next=new LinkedHashMap<>();
            int childDepthBudget=maxLen-(m+1);
            for(PatternData p:cur){
                met.pairAttempts++;
                List<PatternData>bucket=idx.get(p.suffix);if(bucket==null)continue;
                for(PatternData q:bucket){
                    met.compatiblePairs++;
                    double theta=theta(heap,topK);
                    // IMPORTANT: an immediate-child PUB is not enough here because OPF support may
                    // increase again in later descendants. PDUB bounds the whole pair-issued lineage.
                    if(usePDUB){
                        double pdub=Bounds.pairDescendantUpperBound(p,q,t.length,k,w,childDepthBudget);
                        if(pdub+PRUNE_EPS<theta){met.pairDescendantPrunes++;continue;}
                    }
                    for(PatternData r:Fusion.fuse(p,q,t,w,met)){
                        if(r.pattern.length()>=minLen) offer(heap,BaselineOPFMiner.score(r),topK);
                        int remain=maxLen-r.pattern.length();
                        double now=theta(heap,topK);
                        if(remain>0){
                            if(!useDUB || heap.size()<topK || Bounds.descendantUpperBound(r,t.length,k,w,remain)+PRUNE_EPS>=now) next.put(r.pattern,r);
                            else met.branchBoundPrunes++;
                        }
                    }
                }
            }
            cur=new ArrayList<>(next.values());met.expandedPatterns+=cur.size();met.sampleHeap();
        }
        ArrayList<ScoredPattern>ans=new ArrayList<>(heap);ans.sort(BaselineOPFMiner::compareScores);met.runtimeNanos=System.nanoTime()-start;return new MiningResult(ans,met);
    }

    private static List<PatternData> branchFilter(List<PatternData>x,int n,double k,double[]w,int maxLen,PriorityQueue<ScoredPattern>h,int K,Metrics m){
        ArrayList<PatternData>o=new ArrayList<>();double theta=theta(h,K);
        for(PatternData p:x){int d=maxLen-p.pattern.length();if(d<=0||h.size()<K||Bounds.descendantUpperBound(p,n,k,w,d)+PRUNE_EPS>=theta)o.add(p);else m.branchBoundPrunes++;}
        return o;
    }
    private static double theta(PriorityQueue<ScoredPattern>h,int K){return h.size()<K?0.0:h.peek().support();}
    private static void offer(PriorityQueue<ScoredPattern>h,ScoredPattern s,int K){
        if(h.size()<K){h.offer(s);return;}
        if(compareBest(s,h.peek())<0){h.poll();h.offer(s);}
    }
    /** negative means a is better than b */
    private static int compareBest(ScoredPattern a,ScoredPattern b){return BaselineOPFMiner.compareScores(a,b);}
    /** Priority queue root is worst: smaller support; for ties longer/lexicographically larger is worse. */
    private static int compareWorstFirst(ScoredPattern a,ScoredPattern b){
        int c=Double.compare(a.support(),b.support());if(c!=0)return c;return -a.pattern().compareTo(b.pattern());
    }
}
