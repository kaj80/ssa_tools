import hudson.model.*

String labelIWantServersOf = "SSA"; 
String serverList = '';

println(labelIWantServersOf);

for (aSlave in hudson.model.Hudson.instance.slaves) {          
  out.println('Evaluating Server(' + aSlave.name + ') with label = ' + aSlave.getLabelString());  

  if (aSlave.getLabelString().indexOf(labelIWantServersOf ) > -1) {
    serverList += aSlave.name + ' '+ aSlave.getLabelString() + '\n';        
    out.println('Valid server found: ' + aSlave.name);                  
  }    

}

channel = build.workspace.channel;

fp = new hudson.FilePath(channel, build.workspace.toString() + "/nodes.list")

if(fp != null)
{
    fp.write(serverList, null); //writing to file
    String str = fp.readToString(); //reading from file
  	out.println(str);
}

