package org.tkhjopf.core;

public final class Forgetting {
    private Forgetting() {}
    public static double[] weights(int n, double k) {
        if (!(k > 0.0)) throw new IllegalArgumentException("forgetting factor k must be > 0");
        double[] w=new double[n];
        for(int j=0;j<n;j++) w[j]=Math.exp(-k*((n-1)-j));
        return w;
    }
    public static double support(int[] ends, double[] w) {
        double s=0; for(int e:ends) s+=w[e]; return s;
    }
}
