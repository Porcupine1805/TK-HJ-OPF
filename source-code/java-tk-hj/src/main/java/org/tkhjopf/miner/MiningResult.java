package org.tkhjopf.miner;

import org.tkhjopf.model.ScoredPattern;
import org.tkhjopf.metrics.Metrics;
import java.util.List;

public record MiningResult(List<ScoredPattern> patterns, Metrics metrics) {}
