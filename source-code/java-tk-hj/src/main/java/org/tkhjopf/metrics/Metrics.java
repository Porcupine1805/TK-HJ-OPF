package org.tkhjopf.metrics;

public final class Metrics {
    public long pairAttempts;
    public long compatiblePairs;
    public long pairDescendantPrunes;
    public long branchBoundPrunes;
    public long alignedOccurrenceChecks;
    public long generatedPatterns;
    public long expandedPatterns;
    public long runtimeNanos;
    public long approxPeakHeapBytes;
    public void sampleHeap(){
        Runtime r=Runtime.getRuntime();
        long used=r.totalMemory()-r.freeMemory();
        if(used>approxPeakHeapBytes) approxPeakHeapBytes=used;
    }
    public String summary(){
        return "runtime_ms="+(runtimeNanos/1_000_000.0)+
            " pairAttempts="+pairAttempts+" compatiblePairs="+compatiblePairs+
            " pairDescendantPrunes="+pairDescendantPrunes+" branchBoundPrunes="+branchBoundPrunes+
            " alignedChecks="+alignedOccurrenceChecks+" generated="+generatedPatterns+
            " expanded="+expandedPatterns+" peakHeapMB="+(approxPeakHeapBytes/1048576.0);
    }
}
