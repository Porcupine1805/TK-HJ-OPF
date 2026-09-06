package org.tkhjopf.miner;

import org.tkhjopf.core.*;
import org.tkhjopf.model.*;
import org.tkhjopf.metrics.Metrics;
import java.util.*;

/**
 * Exact semantic baseline for the new top-k problem: enumerate every observed OP pattern
 * by hash-indexed compatible-pair fusion, never use a top-k bound to prune the search, and
 * retain only the best K scores in a heap.  This isolates the value of PDUB/DUB from HJ itself.
 */
public final class ExhaustiveHJTopKMiner {
    public MiningResult mine(double[] t,double k,int topK,int minLen,int maxLen){
        if(topK<=0)throw new IllegalArgumentException("topK must be positive");
        if(minLen<2)throw new IllegalArgumentException("minLen must be >= 2");
        long start=System.nanoTime();Metrics met=new Metrics();double[]w=Forgetting.weights(t.length,k);
        if(maxLen<=0||maxLen>t.length)maxLen=t.length;
        if(minLen>maxLen)throw new IllegalArgumentException("minLen > maxLen");
        PriorityQueue<ScoredPattern> heap=new PriorityQueue<>(topK,ExhaustiveHJTopKMiner::compareWorstFirst);
        List<PatternData> cur=SeedFactory.length2(t,w);
        if(minLen<=2)for(PatternData p:cur)offer(heap,BaselineOPFMiner.score(p),topK);
        met.sampleHeap();
        for(int m=2;m<maxLen&&!cur.isEmpty();m++){
            Map<IntArrayKey,List<PatternData>> idx=new HashMap<>();
            for(PatternData q:cur)idx.computeIfAbsent(q.prefix,z->new ArrayList<>()).add(q);
            LinkedHashMap<Pattern,PatternData> next=new LinkedHashMap<>();
            for(PatternData p:cur){
                met.pairAttempts++;
                List<PatternData> bucket=idx.get(p.suffix); if(bucket==null)continue;
                for(PatternData q:bucket){
                    met.compatiblePairs++;
                    for(PatternData r:Fusion.fuse(p,q,t,w,met)){
                        if(r.pattern.length()>=minLen)offer(heap,BaselineOPFMiner.score(r),topK);
                        next.put(r.pattern,r);
                    }
                }
            }
            cur=new ArrayList<>(next.values());met.expandedPatterns+=cur.size();met.sampleHeap();
        }
        ArrayList<ScoredPattern> ans=new ArrayList<>(heap);ans.sort(BaselineOPFMiner::compareScores);
        met.runtimeNanos=System.nanoTime()-start;return new MiningResult(ans,met);
    }
    private static void offer(PriorityQueue<ScoredPattern>h,ScoredPattern s,int K){
        if(h.size()<K){h.offer(s);return;} if(BaselineOPFMiner.compareScores(s,h.peek())<0){h.poll();h.offer(s);}
    }
    private static int compareWorstFirst(ScoredPattern a,ScoredPattern b){
        int c=Double.compare(a.support(),b.support());if(c!=0)return c;return -a.pattern().compareTo(b.pattern());
    }
}
