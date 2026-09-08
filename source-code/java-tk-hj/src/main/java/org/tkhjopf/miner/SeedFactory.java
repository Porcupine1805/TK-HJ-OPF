package org.tkhjopf.miner;

import org.tkhjopf.core.*;
import org.tkhjopf.model.PatternData;
import java.util.*;

public final class SeedFactory {
    private SeedFactory() {}
    public static List<PatternData> length2(double[] t,double[] w){
        ArrayList<Integer> up=new ArrayList<>(),down=new ArrayList<>();
        for(int j=1;j<t.length;j++){
            int c=Double.compare(t[j-1],t[j]);
            if(c<0) up.add(j); else if(c>0) down.add(j);
        }
        ArrayList<PatternData> out=new ArrayList<>();
        if(!up.isEmpty()) out.add(new PatternData(new Pattern(new int[]{1,2}),toInt(up),w));
        if(!down.isEmpty()) out.add(new PatternData(new Pattern(new int[]{2,1}),toInt(down),w));
        return out;
    }
    private static int[] toInt(List<Integer> x){int[] a=new int[x.size()];for(int i=0;i<a.length;i++)a[i]=x.get(i);return a;}
}
