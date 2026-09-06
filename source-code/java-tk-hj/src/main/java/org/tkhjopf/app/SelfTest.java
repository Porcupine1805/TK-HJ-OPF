package org.tkhjopf.app;

import org.tkhjopf.miner.*;import org.tkhjopf.model.ScoredPattern;
import java.util.*;
public final class SelfTest{
 public static void main(String[]args){
  double[]t={15,32,29,27,34,33,25,20,28,23};int K=5;MiningResult x=new TKHJOPFMiner().mine(t,0.1,K,10),b=new BruteForceMiner().topK(t,0.1,K,10);
  if(x.patterns().size()!=b.patterns().size())fail("size");
  for(int i=0;i<K;i++){ScoredPattern a=x.patterns().get(i),z=b.patterns().get(i);if(!a.pattern().equals(z.pattern())||Math.abs(a.support()-z.support())>1e-10)fail("rank "+i+" got "+a+" expected "+z);}
  String[]expect={"(2,1)","(1,3,2)","(3,2,1)","(1,2)","(2,1,3)"};for(int i=0;i<K;i++)if(!x.patterns().get(i).pattern().compact().equals(expect[i]))fail("example order");
  System.out.println("SELF-TEST PASSED: TK-HJ-OPF equals brute force on the OPF running example.");
 }
 private static void fail(String s){throw new AssertionError(s);}
}
