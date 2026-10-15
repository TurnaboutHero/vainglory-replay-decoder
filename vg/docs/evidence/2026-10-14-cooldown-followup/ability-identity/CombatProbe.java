//@category CombatResearch
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;
public class CombatProbe extends GhidraScript {
 public void run() throws Exception {
  String[] args=getScriptArgs();
  File out=new File(args[0]);out.mkdirs();
  DecompInterface d=new DecompInterface();d.openProgram(currentProgram);
  for(int i=1;i<args.length;i++){
   String s=args[i];
   if(s.startsWith("r:")){currentProgram.getFunctionManager().removeFunction(toAddr(s.substring(2)));continue;}
   if(s.startsWith("v:")){
    Address a=toAddr(s.substring(2)); try(PrintWriter w=new PrintWriter(new File(out,"vtable_"+a+".txt"))){
     for(int j=0;j<28;j++){Address q=a.add(j*4);w.printf("%s %08x%n",q,getInt(q));}
    }continue;
   }
   Address a=toAddr(s);disassemble(a);Function f=getFunctionAt(a);if(f==null)f=createFunction(a,null);
   try(PrintWriter w=new PrintWriter(new File(out,s+".txt"))){
    if(f==null){w.println("NO FUNCTION");continue;}
    w.println("ENTRY "+f.getEntryPoint()+" BODY "+f.getBody());
    DecompileResults r=d.decompileFunction(f,60,monitor);
    w.println(r.decompileCompleted()?r.getDecompiledFunction().getC():r.getErrorMessage());
    w.println("\nINSTRUCTIONS");
    InstructionIterator it=currentProgram.getListing().getInstructions(f.getBody(),true);
    while(it.hasNext()){Instruction ins=it.next();w.println(ins.getAddress()+" "+ins);}
   }
  }d.dispose();
 }
}
