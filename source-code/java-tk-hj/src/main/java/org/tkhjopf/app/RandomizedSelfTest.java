package org.tkhjopf.app;

import org.tkhjopf.miner.*;
import org.tkhjopf.model.ScoredPattern;
import java.util.*;

/** Deterministic property test: exact TK-HJ-OPF must equal exhaustive window enumeration on small tie-free series. */
public final class RandomizedSelfTest {
    public static void main(String[] args) {
        Random rnd=new Random(20260818L);
        int cases=0;
        for(int n=5;n<=9;n++){
            for(int trial=0;trial<20;trial++){
                double[] t=randomPermutationSeries(n,rnd);
                for(double k:new double[]{0.03,0.1,0.3}){
                    for(int minLen:new int[]{2,3}){
                        if(minLen>n) continue;
                        for(int K:new int[]{1,2,3,5}){
                            int kk=Math.min(K,1000000);
                            MiningResult a=new TKHJOPFMiner().mine(t,k,kk,minLen,n,true,true,true);
                            MiningResult naive=new TKHJOPFMiner().mine(t,k,kk,minLen,n,true,true,false);
                            MiningResult b=new BruteForceMiner().topK(t,k,kk,minLen,n);
                            assertSame(a,b,n,trial,k,minLen,K);
                            assertSame(a,naive,n,trial,k,minLen,K);
                            if(a.metrics().pairDescendantPrunes!=naive.metrics().pairDescendantPrunes
                                    || a.metrics().alignedOccurrenceChecks!=naive.metrics().alignedOccurrenceChecks
                                    || a.metrics().branchBoundPrunes!=naive.metrics().branchBoundPrunes)
                                fail("profile vs naive counters",n,trial,k,minLen,K,a,naive);
                            cases++;
                        }
                    }
                }
            }
        }
        System.out.println("RANDOMIZED SELF-TEST PASSED: "+cases+" exact comparisons against brute force.");
    }

    private static double[] randomPermutationSeries(int n,Random rnd){
        ArrayList<Integer> v=new ArrayList<>();for(int i=1;i<=n;i++)v.add(i);
        Collections.shuffle(v,rnd);double[] t=new double[n];for(int i=0;i<n;i++)t[i]=v.get(i);return t;
    }

    private static void assertSame(MiningResult a,MiningResult b,int n,int trial,double k,int minLen,int K){
        if(a.patterns().size()!=b.patterns().size())fail("size",n,trial,k,minLen,K,a,b);
        for(int i=0;i<a.patterns().size();i++){
            ScoredPattern x=a.patterns().get(i),y=b.patterns().get(i);
            if(!x.pattern().equals(y.pattern())||Math.abs(x.support()-y.support())>1e-10)
                fail("rank="+i,n,trial,k,minLen,K,a,b);
        }
    }
    private static void fail(String why,int n,int trial,double k,int minLen,int K,MiningResult a,MiningResult b){
        throw new AssertionError(why+" n="+n+" trial="+trial+" k="+k+" minLen="+minLen+" K="+K+"\nTK="+a.patterns()+"\nBF="+b.patterns());
    }
}
