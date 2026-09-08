package org.tkhjopf.app;

import org.tkhjopf.io.TimeSeriesIO;import org.tkhjopf.miner.*;import org.tkhjopf.model.ScoredPattern;
import java.nio.file.*;import java.util.*;
public final class Main{
 public static void main(String[]args)throws Exception{
  Map<String,String>a=parse(args);String mode=a.getOrDefault("mode","tk");Path input=Path.of(req(a,"input"));double[]t=TimeSeriesIO.read(input);
  double k=Double.parseDouble(a.getOrDefault("forgetting",Double.toString(1.0/t.length)));int minLen=Integer.parseInt(a.getOrDefault("minLen","2"));int max=Integer.parseInt(a.getOrDefault("maxLen","0"));MiningResult r;
  switch(mode){case"baseline"->r=new BaselineOPFMiner().mine(t,k,Double.parseDouble(a.getOrDefault("minSup","1.5")),max);case"hj"->r=new HJOPFMiner().mine(t,k,Double.parseDouble(a.getOrDefault("minSup","1.5")),max);case"hjtopk"->r=new ExhaustiveHJTopKMiner().mine(t,k,Integer.parseInt(a.getOrDefault("topK","10")),minLen,max);case"tk"->r=new TKHJOPFMiner().mine(t,k,Integer.parseInt(a.getOrDefault("topK","10")),minLen,max,true,true,true);case"tk-naive"->r=new TKHJOPFMiner().mine(t,k,Integer.parseInt(a.getOrDefault("topK","10")),minLen,max,true,true,false);case"tk-no-pdub"->r=new TKHJOPFMiner().mine(t,k,Integer.parseInt(a.getOrDefault("topK","10")),minLen,max,false,true,true);case"tk-no-dub"->r=new TKHJOPFMiner().mine(t,k,Integer.parseInt(a.getOrDefault("topK","10")),minLen,max,true,false,true);case"tk-no-bounds"->r=new TKHJOPFMiner().mine(t,k,Integer.parseInt(a.getOrDefault("topK","10")),minLen,max,false,false,true);default->throw new IllegalArgumentException("mode=baseline|hj|hjtopk|tk|tk-naive|tk-no-pdub|tk-no-dub|tk-no-bounds");}
  int rank=1;for(ScoredPattern p:r.patterns())System.out.printf(Locale.ROOT,"%d\t%s\t%.12f\t%s%n",rank++,p.pattern().compact(),p.support(),Arrays.toString(Arrays.stream(p.occurrences()).map(x->x+1).toArray()));System.err.println(r.metrics().summary());
 }
 private static Map<String,String>parse(String[]x){Map<String,String>m=new HashMap<>();for(int i=0;i<x.length;i++){if(x[i].startsWith("--")){String k=x[i].substring(2);String v=(i+1<x.length&&!x[i+1].startsWith("--"))?x[++i]:"true";m.put(k,v);}}return m;}
 private static String req(Map<String,String>m,String k){if(!m.containsKey(k))throw new IllegalArgumentException("missing --"+k);return m.get(k);}
}
