package org.tkhjopf.io;

import java.io.*;import java.nio.file.*;import java.util.*;
public final class TimeSeriesIO{
 private TimeSeriesIO(){}
 public static double[] read(Path p)throws IOException{
  String s=Files.readString(p);String[]tok=s.trim().split("[\\s,;]+");double[]a=new double[tok.length];for(int i=0;i<a.length;i++)a[i]=Double.parseDouble(tok[i]);return a;
 }
}
