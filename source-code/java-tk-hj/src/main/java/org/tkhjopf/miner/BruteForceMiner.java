package org.tkhjopf.miner;

import org.tkhjopf.core.*;
import org.tkhjopf.model.*;
import org.tkhjopf.metrics.Metrics;
import java.util.*;

public final class BruteForceMiner {
    public MiningResult topK(double[]t,double k,int K,int maxLen){ return topK(t,k,K,2,maxLen); }
    public MiningResult topK(double[]t,double k,int K,int minLen,int maxLen){
        long st=System.nanoTime();Metrics met=new Metrics();double[]w=Forgetting.weights(t.length,k);if(maxLen<=0||maxLen>t.length)maxLen=t.length;
        if(minLen<2||minLen>maxLen)throw new IllegalArgumentException("invalid length range");
        Map<Pattern,List<Integer>>map=new HashMap<>();
        for(int m=minLen;m<=maxLen;m++)for(int s=0;s+m<=t.length;s++){
            double[]win=Arrays.copyOfRange(t,s,s+m);Pattern p=RankEncoding.normalize(win);if(p!=null)map.computeIfAbsent(p,z->new ArrayList<>()).add(s+m-1);
        }
        ArrayList<ScoredPattern>a=new ArrayList<>();for(var e:map.entrySet()){int[]o=e.getValue().stream().mapToInt(i->i).toArray();a.add(new ScoredPattern(e.getKey(),Forgetting.support(o,w),o));}
        a.sort(BaselineOPFMiner::compareScores);if(a.size()>K)a=new ArrayList<>(a.subList(0,K));met.runtimeNanos=System.nanoTime()-st;return new MiningResult(a,met);
    }
}
