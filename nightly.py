#!/usr/bin/python

#
# Rajarshi Guha <rajarshi@presidency.com>
# 04/30/2006
#
# Requires a Unix system, for now
#
# Requires on the path:   java, ant, svn, nice, rm, tar
# Optionally on the path: dot (from graphviz)
#
# Python requirements: Python 2.4, libxml & libxslt bindings
#
# Environment requirements: JAVA_HOME and ANT_HOME should be set
#
# Also you should have Beanshell and JGraphT installed and specified
# in the classpath variable below. However if specified as "" or None
# then no dependency graph is generated
#
# Update 05/01/2006 - Added suggestions from Egon: link to sf.net,
#                     added a title to the HTML page, links to
#                     build output, link to a JUnit summary, link
#                     to dependency graphs
# Update 05/05/2006 - Added JAPI comparison. Checked for required
#                     executables and env vars
# Update 05/07/2006 - Added a command line option to prevent mail
#                     from being sent. Also replaced the system() to
#                     tar with calls to the tarfile python module.
#                     Added some more checks
#

import string, sys, os, os.path, time, re, glob, shutil
import tarfile
from email.MIMEText import MIMEText
import email.Utils
import smtplib

#################################################################
#
# User definable variables
#
#################################################################

# should point to an SVN repo, within which doing
# ant dist-all should work
nightly_repo = '/home/rajarshi/src/java/cdk-nightly/cdk/'

# should point to a directory in which this script
# is to be placed and will contain log files
nightly_dir = '/home/rajarshi/src/java/cdk-nightly/'

# points to a web accessible directory where the
# nightly build site will be generated
nightly_web = '/home/rajarshi/public_html/code/java/nightly/'
#nightly_web = '/home/rajarshi/public_html/tmp/'



# Optional
# required to generate the dependency graph. Should
# contain the path to the BeanShell and JGraphT jar files
# if not required set to "" or None
classpath = '/home/rajarshi/src/java/beanshell/bsh.jar:/home/rajarshi/src/java/cdk/trunk/cdk/jar/jgrapht-0.6.0.jar'

# Optional
# path to the japitools directory for API comparison
# if not required set to "" or None
japitools_path = '/home/rajarshi/src/java/japitools'

# Optional
# path to the last stable CDK distribution jar
# if not required set to "" or None
last_stable = '/home/rajarshi/src/java/cdk-20050826.jar'

per_line = 4

# Optional
# variables required for sending mail, if desired.
# should be self explanatory. Set to "" or None if
# you dont want to send mail
smtpServerName = 'smtp.psu.edu'
fromName = 'nightly.py <rajarshi@presidency.com>'
toName = 'cdk-devel@lists.sourceforge.net'

#################################################################
#
# NO NEED TO CHANGE ANYTHING BELOW HERE
#
#################################################################

today = time.localtime()
todayStr = '%04d%02d%02d' % (today[0], today[1], today[2])
todayNice = '%04d-%02d-%02d' % (today[0], today[1], today[2])
dryRun = False
haveXSLT = True
noMail = False

# check to see if we have libxml2 and libxslt
try:
    import libxml2
    import libxslt
except ImportError:
    haveXSLT = False
    print 'Will not tranlate PMD XML output'

def sendMail(message):
    if fromName == "" or fromName == None \
       or toName == "" or toName == None \
       or smtpServerName == "" or smtpServerName == None:
        print 'Skipping mail'
        return 
    
    try:        
        msg = MIMEText(message)
        msg['Subject'] = 'CDK Nightly Build Failed %s' % (todayNice)
        msg['Message-id'] = email.Utils.make_msgid()
        msg['From'] = fromName
        msg['To'] = toName

        server = smtplib.SMTP(smtpServerName)
        server.sendmail(fromName, toName, msg.as_string())
        server.quit()
        print 'Sent mail to %s' % (toName)
    except Exception, e:
        print e
    
def transformXML2HTML(src, dest):
    if haveXSLT: # if we have the proper libs do the xform
        xsltFile = os.path.join(nightly_repo,'pmd','wz-pmd-report.xslt')
        styleDoc = libxml2.parseFile(xsltFile)
        style = libxslt.parseStylesheetDoc(styleDoc)
        doc = libxml2.parseFile(src)
        result = style.applyStylesheet(doc, None)
        htmlString = style.saveResultToString(result)        
        style.freeStylesheet()
        doc.freeDoc()
        result.freeDoc()

        # we need to add a bit to the HTML output to indicate what file was processed
        prefix = os.path.basename(dest).split('.')[0]
        htmlString = re.sub('Report</div>', 'Report [<i>module - %s</i>]</div>' % (prefix), htmlString)
        f = open(dest, 'w')
        f.write(htmlString)
        f.close()
        
    else: # cannot xform, so just copy the XML file
        shutil.copyfile(src, dest)
    
def writeJunitSummaryHTML(stats):
    summary = """
    <html>
    <head>
    <title>CDK JUnit Test Summary - %s</title>
    </head>
    <body>
    <center>
    <h2>CDK JUnit Test Summary (%s)</h2>
    <table border=0 cellspacing=5>
    <thead>
    <tr>
    <td><b>Module</b></td><td><b>Number of Tests</b></td><td><b>Failed</b></td><td><b>Errors</b></td>
    </tr>
    </thead>
    <tr>
    <td colspan=4><hr></td>
    </tr>
    """ % (todayNice, todayNice)
    for entry in stats:
        summary = summary + "<tr>"
        summary = summary + "<td align=\"left\">%s</td>" % (entry[0])
        for i in entry[1:]:
            summary = summary + "<td align=\"center\">%s</td>" % (i)
        summary = summary + "</tr>"
    summary = summary + """
    <tr>
    <td colspan=4><hr></td>
    </tr>
    </table>
    </center>
    </body>
    </html>"""
    return summary

def parseJunitOutput(summaryFile):
    f = open(os.path.join(nightly_dir,'test.log'), 'r')
    stats = []
    foundModuleEntry = False
    while True:
        line = f.readline()
        if not line: break
        if string.find(line, 'test-module') == 0:
            foundModuleEntry = True
        if foundModuleEntry:
            foundModuleEntry = False
            moduleName = f.readline()
            moduleStats = None
            while True:
                moduleStats = f.readline()
                if string.find(moduleStats, '[junit] Tests run:') != -1: break

            # parse the stats and name of the module
            moduleStats = moduleStats.split()
            nTest = moduleStats[3][:-1]
            nFail = moduleStats[5][:-1]
            nError = moduleStats[7][:-1]
            stats.append( (moduleName.split()[5], nTest, nFail, nError) )
    f.close()

    # get an HTML summary
    summary = writeJunitSummaryHTML(stats)
    
    # write out this HTML
    fileName = os.path.join(nightly_web, summaryFile)
    f = open(fileName, 'w')
    f.write(summary)
    f.close()
    
def checkIfAntJobFailed(logFileName):
    """
    Returns True if the specified log file does
    not contain the string 'BUILD SUCCESSFUL'
    otherwise returns False
    """
    f = open(logFileName, 'r')
    loglines = f.readlines()
    f.close()
    loglines = string.join(loglines)
    if loglines.find('BUILD SUCCESSFUL') == -1:
        return True
    else: return False

def getLogFilePath(logFileName):
    """
    Creates the full path for a specified log file.

    The log files are always placed in the NIGHTLY_DIR which can
    be changed by the user"""
    
    return os.path.join(nightly_dir, logFileName)

def updateSVN():
    olddir = os.getcwd()
    os.chdir(nightly_repo)
    status = os.system('svn update > %s' % getLogFilePath('svn.log'))
    if status == 0:
        print 'svn ok'
        os.chdir(olddir)        
        return True
    else:
        print 'svn failed'
        os.chdir(olddir)
        return False

def runAntJob(cmdLine, logFileName, jobName):
    olddir = os.getcwd()
    os.chdir(nightly_repo)
    os.system('%s > %s' % (cmdLine, getLogFilePath(logFileName)))

    if not os.path.exists(getLogFilePath(logFileName)):
        print '%s failed' % (jobName)
        return False
        
    if checkIfAntJobFailed( getLogFilePath(logFileName) ):
        print '%s failed' % (jobName)
        os.chdir(olddir)
        return False
    else:
        print '%s ok' % (jobName)
        os.chdir(olddir)
        return True

def generateCDKDepGraph(page):
    olddir = os.getcwd()
    os.chdir(nightly_repo)

    if classpath == "" or classpath == None:
        print 'classpath not specified. Skipping dependency graph'
        return page
    
    if string.find(classpath, 'bsh.jar') == -1 or \
           string.find(classpath, 'jgrapht') == -1:
        print 'Did not find bsh.jar or the jgrapht jar in \'classpath\''
        return page

    if not executableExists('dot'):
        print 'dot not found. Skipping dependency graph'
        return page
    
    os.system('java -cp %s bsh.Interpreter deptodot.bsh > /tmp/cdkdep.dot' % (classpath))
    os.system('dot -Tpng /tmp/cdkdep.dot -o %s/cdkdep.png' % (nightly_web))
    os.system('dot -Tps /tmp/cdkdep.dot -o %s/cdkdep.ps' % (nightly_web))
    os.unlink('/tmp/cdkdep.dot')
    page = page + """
    <tr>
    <td valign=\"top\">Dependency Graph:</td>
    <td>
    <a href=\"cdkdep.png\">PNG</a>
    <a href=\"cdkdep.ps\">PS</a>
    </td>
    </tr>
    """
    os.chdir(olddir)
    return page

def writeNightlyPage(contents):
    contents = contents + """
    <tr><td colspan=3><hr></td></tr>
    <tr>
    <td valign=\"top\"><i>Build details</i></td>
    <td><i>Fedora Core 5<br>
    Sun JDK 1.5.0<br>
    Ant 1.6.2</i></td>
    </tr>
    </table>
    <br><br><br>Generated by <a href=\"nightly.py\">nightly.py</a>
    <p>
<a href=\"http://sourceforge.net/projects/cdk/\"><img alt=\"SourceForge.net Logo\" 
border=\"0\" height=\"31\" width=\"88\" 
src=\"http://sourceforge.net/sflogo.php?group_id=20024&type=5&type=1\"></a>
    </center>
    </body>
    </html>
    """
    f = open(os.path.join(nightly_web, 'index.html'), 'w')
    f.write(contents)
    f.close()

def writeTemporaryPage():
    f = open(os.path.join(nightly_web, 'index.html'), 'w')
    f.write("""
     <html>
    <head>
      <title>
      CDK Nightly Build
      </title>
      <style>
      <!--
        tr:hover { background-color: #efefef; }
      //-->
      </style>
    <head>
    <body>
    <center>
    <h2>CDK Nightly Build</h2>
    <p>
    <br><br>
    Regenerating Build - Please come back in a while
    <center>
    </body>
    </html>""")
    f.close()
    
def copyLogFile(fileName, srcDir, destDir, page, extra=None):
    if os.path.exists( os.path.join(srcDir, fileName) ):
        shutil.copyfile(os.path.join(srcDir, fileName),
                        os.path.join(destDir, fileName))            
        page = page + "<td valign=\"top\"><a href=\"%s\">%s</a></td></tr>" % (fileName, fileName)
    else:
        page = page + "</tr>"
    return page

def executableExists(executable):
    found = False
    paths = os.environ['PATH']
    paths = paths.split(os.pathsep)
    if len(paths) == 0: return False
    for aPath in paths:
        testPath = os.path.join(aPath, executable)
        if os.path.exists(testPath) and os.path.isfile(testPath):
            found = True
            break
    return found

def generateJAPI(page):
    olddir = os.getcwd()
    os.chdir(nightly_dir)
    
    if japitools_path == "" or japitools_path == None:
        print 'japitools_path not specified. Skipping japi'
        return page

    java_home = None
    try:
        java_home = os.environ['JAVA_HOME']
    except KeyError, ke:
        print 'java_home not specified. Skipping japi'
        return page
    
    if last_stable == "" or last_stable == None:
        print 'last_stable not specified. Skipping japi'
        return page

    # get the paths to the japi binaries
    japize = os.path.join(japitools_path, 'bin', 'japize')
    japicompat = os.path.join(japitools_path, 'bin', 'japicompat')

    # get path to rt.jar
    rtjar = None
    if os.path.exists(os.path.join(java_home, 'jre', 'lib', 'rt.jar')):
        rtjar = os.path.join(java_home, 'jre', 'lib', 'rt.jar')
    elif os.path.exists(os.path.join(java_home, 'lib', 'rt.jar')):
        rtjar = os.path.join(java_home, 'jre', 'lib', 'rt.jar')

    if rtjar == None:
        print 'Cannot find rt.jar. Skipping japi comparison'
        return page

    oldName = os.path.basename(last_stable).split('.')[0]
    oldJapize = os.path.join(nightly_dir, '%s.japi.gz' % (oldName))
    newName = 'cdk-svn-%s' % (todayStr)    
    newJar  = os.path.join(nightly_repo, 'dist', 'jar', 'cdk-svn-%s.jar' % (todayStr))
    newJapize = os.path.join(nightly_dir, '%s.japi.gz' % (newName)) 

    # run japize on the old cdk and the new one
    os.system('%s as %s apis %s %s +org.openscience.cdk 2> japize.log'
              % (japize, oldJapize, last_stable, rtjar))
    os.system('%s as %s apis %s %s +org.openscience.cdk 2>> japize.log'
              % (japize, newJapize, newJar, rtjar))

    # do the comparison
    os.system('%s -vh -o apicomp.html %s %s 2> japi.log'
              % (japicompat, oldJapize, newJapize))

    # copy output
    srcFile = os.path.join(nightly_dir, 'apicomp.html')
    destFile = os.path.join(nightly_web, 'apicomp.html')
    shutil.copyfile(srcFile, destFile)

    # copy japi css so we get a nice webpage
    srcFile = os.path.join(japitools_path, 'design', 'japi.css')
    destFile = os.path.join(nightly_web, 'japi.css')
    shutil.copyfile(srcFile, destFile)

    # copy the comparison log file
    srcFile = os.path.join(nightly_dir, 'japi.log')
    destFile = os.path.join(nightly_web, 'japi.log')
    shutil.copyfile(srcFile, destFile)

    # make an entry on the page
    page = page + """
        <tr>
        <td><a href=\"http://www.kaffe.org/~stuart/japi/\">JAPI Comparison</td>
        <td><a href=\"apicomp.html\">Summary</a></td>
        <td><a href=\"japi.log\">japicompat.log</a></td>
        </tr>
    """
    print 'japi ok'

    # cleanup
    os.unlink(newJapize)
    os.unlink(oldJapize)
    os.unlink('apicomp.html')
    
    os.chdir(olddir)
    
    return page

if __name__ == '__main__':
    if 'help' in sys.argv:
        print """
        Usage: nightly.py [ARGS]

        ARGS can be:

          help   - this message
          dryrun - do a dry run. This does not sync with SVN or run ant tasks. It is expected
                   that you have stuff from a previous run available and is mainly for testing
          nomail - if specified no mail will be sent in response to build errors
        """
        sys.exit(0)

    # check for the presence of required executable
    executableList = ['java', 'ant', 'tar', 'nice', 'svn', 'rm']
    ret = map( executableExists, executableList )
    if False in executableList:
        print 'Could not find one or more required executables: '+executableList
        sys.exit(-1)

    # check for certain environment variables
    try:
        tmp = os.environ['JAVA_HOME']
        tmp = os.environ['ANT_HOME']
    except KeyError, ke:
        print 'JAVA_HOME & ANT_HOME must be set in the environment'
        sys.exit(-1)
        
    # are we going to do a dry run?
    if 'dryrun' in [x.lower() for x in sys.argv] or 'dry' in [x.lower() for x in sys.argv]:
        dryRun = True

    if 'nomail' in [x.lower() for x in sys.argv]:
        noMail = True


    # print out some status stuff
    print """
    Variable settings
    
    nightly_repo = %s
    nightly_dir  = %s
    nightly_web  = %s
    """ % (nightly_repo, nightly_dir, nightly_web)
    
    successDist = True
    successTest = True
    successJavadoc = True
    successDoccheck = True
    successPMD = True
    successSVN = True
    
    start_dir = os.getcwd()
    os.chdir(nightly_dir)

    if not dryRun:
        # clean up log files in the run dir
        os.system('rm -f *.log')

        # go into the repo and sync with SVN
        successSVN = updateSVN()

        # if we failed, report it and use previous build info
        if not successSVN:
            print 'Could not connect to SVN. Skipping nightly build'
            f = open(os.path.join(nightly_web, 'index.html'), 'r')
            lines = string.join(f.readlines())
            f.close()
            newlines = re.sub("<h2>CDK Nightly Build",
                          """<center><b><h3>Could not connect to SVN. Using yesterdays build</h3></b></center>
                          <hr>
                          <p>
                          <h2>CDK Nightly Build""", lines)
            f = open(os.path.join(nightly_web, 'index.html'), 'w')
            f.write(newlines)
            f.close()
            os.chdir(start_dir)
            sys.exit(0)


        # compile the distro
        successDist = runAntJob('nice -n 19 ant clean dist-large', 'build.log', 'distro')
        if successDist: # if we compiled, do the rest of the stuff
            successTest = runAntJob('export R_HOME=/usr/local/lib/R && nice -n 19 ant -DrunSlowTests=false test-all', 'test.log', 'test') 
            successJavadoc = runAntJob('nice -n 19 ant -f javadoc.xml', 'javadoc.log', 'javadoc')
            successDoccheck = runAntJob('nice -n 19 ant -f javadoc.xml doccheck', 'doccheck.log', 'doccheck')
            successPMD = runAntJob('nice -n 19 ant -f pmd.xml pmd', 'pmd.log', 'pmd')
        else: # if the distro could not be built, there's not much use doing the other stuff
            print 'Distro compile failed. Generating error page'
            srcFile = os.path.join(nightly_dir, 'build.log')
            destFile = os.path.join(nightly_web, 'build.log.fail')
            shutil.copyfile(srcFile, destFile)
            f = open(os.path.join(nightly_web, 'index.html'), 'r')
            lines = string.join(f.readlines())
            f.close()
            newlines = re.sub("<h2>CDK Nightly Build",
                          """<center><b><h3>Could not compile the sources -
                          <a href=\"build.log.fail\">build.log</a>
                          </h3></b></center>
                          <hr>
                          <p>
                          <h2>CDK Nightly Build""", lines)
            f = open(os.path.join(nightly_web, 'index.html'), 'w')
            f.write(newlines)
            f.close()

            # before finishing send of an email with the last 20 lines of build.log
            f = open('build.log', 'r')
            lines = f.readlines()
            f.close()
            if not noMail: sendMail(string.join(lines[-20:]))

            # finally done!
            os.chdir(start_dir)
            sys.exit(0)
    else:
        print 'Doing dry run'





    # so we have done a build (hopefully). Get rid of the old stuff
    # and set up a temporary page.    
    os.system('rm -rf %s/*' % (nightly_web))
    writeTemporaryPage()

    page = """
    <html>
    <head>
      <title>
      CDK Nightly Build - %s
      </title>
      <style>
      <!--
        tr:hover { background-color: #efefef; }
      //-->
      </style>
    <head>
    <body>
    <center>
    <h2>CDK Nightly Build - %s</h2>
    <table border=0 cellspacing=5>
    <thead>
    <tr>
    <th></th>
    <th></th>
    <th>Extra Info</th>
    </tr>
    </thead>
    """ % (todayNice, todayNice)

    # lets now make the web site for nightly builds
    if successDist:
        distSrc = os.path.join(nightly_repo, 'dist', 'jar', 'cdk-svn-%s.jar' % (todayStr))
        distDest = os.path.join(nightly_web, 'cdk-svn-%s.jar' % (todayStr))
        shutil.copyfile(distSrc, distDest)
        page = page + """
        <tr>
        <td>
        Combined CDK jar files:</td><td> <a href=\"cdk-svn-%s.jar\">cdk-svn-%s.jar</a></td>
        """ % (todayStr, todayStr)
        
        # check whether we can copy the run output
        page = copyLogFile('build.log', nightly_dir, nightly_web, page)
    else:
        pass

    # Lets tar up the java docs and put them away
    if successJavadoc:
        destFile = os.path.join(nightly_web, 'javadoc-%s.tgz' % (todayStr))

        # tar up the javadocs
        olddir = os.getcwd()
        os.chdir(os.path.join(nightly_repo,'doc'))
        tfile = tarfile.open(destFile, 'w:gz')
        tfile.add('api')
        tfile.close()
        os.chdir(olddir)
        
        shutil.copytree('%s/doc/api' % (nightly_repo),
                        '%s/api' % (nightly_web))                
        page = page + """
        <tr>
        <td valign=\"top\">Javadocs:</td>
        <td><a href=\"javadoc-%s.tgz\">Tarball</a><br>
        <a href=\"api\">Browse online</a></td>
        """ % (todayStr)

        # check whether we can copy the run output
        page = copyLogFile('javadoc.log', nightly_dir, nightly_web, page)
        page = page + "<tr><td colspan=3><hr></td></tr>"
    else:
        page = page + """
        <tr>
        <td valign=\"top\">Javadocs:</td>
        <td bgcolor=\"#ea3f3f\"><b>FAILED</b></td>
        """
        page = copyLogFile('javadoc.log', nightly_dir, nightly_web, page)                
        page = page + "<tr><td colspan=3><hr></td></tr>"

        
    # generate the dependency graph entry
    page = generateCDKDepGraph(page)

    # get the JUnit test results
    if successTest:

        # make the directory for reports
        testDir = os.path.join(nightly_web, 'test')
        os.mkdir(testDir)

        # copy the individual report files
        reportFiles = glob.glob(os.path.join(nightly_repo, 'reports', 'result-*'))
        for report in reportFiles:
            dest = os.path.join(testDir, os.path.basename(report))
            shutil.copyfile(report, dest)

        page = page + """
        <tr>
        <td valign=\"top\"><a href=\"http://www.junit.org/index.htm\">JUnit</a> results:</td><td> """
        repFiles = glob.glob(os.path.join(nightly_repo,'reports/result-*.txt'))
        repFiles.sort()
        count = 1
        for repFile in repFiles:
            title = string.split(os.path.basename(repFile),'.')[0]
            title = string.split(title, '-')[1]
            page = page+"""
        <a href=\"test/%s\">%s</a>""" % (os.path.basename(repFile), title)
            if count % per_line == 0:
                page = page+ "<br>"
            count += 1    
        page = page + "</td>"

        # summarize JUnit test results - it will go into nightly_web
        parseJunitOutput('junitsummary.html')
        
        # check whether we can copy the run output and link to the summary
        if os.path.exists( os.path.join(nightly_dir, 'test.log') ):
            shutil.copyfile(os.path.join(nightly_dir, 'test.log'),
                            os.path.join(nightly_web, 'test.log'))            
            page = page + """
            <td valign=\"top\">
            <a href=\"test.log\">test.log</a><br>
            <a href=\"junitsummary.html\">Summary</a>
            </td></tr>
            """
        else: page = page + "</tr>"
    else:
        page = page + """
        <tr>
        <td valign=\"top\"><a href=\"http://www.junit.org/index.htm\">JUnit</a> results:</td>
        <td bgcolor='#ea3f3f'><b>FAILED</b></td>
        """
        if os.path.exists( os.path.join(nightly_dir, 'test.log') ):
            shutil.copyfile(os.path.join(nightly_dir, 'test.log'),
                            os.path.join(nightly_web, 'test.log'))            
            page = page + """
            <td valign=\"top\">
            <a href=\"test.log\">test.log</a>
            </td></tr>
            """
        else: page = page + "</tr>"        

    # get the results of doccheck
    if successDoccheck:
        shutil.copytree('%s/reports/javadoc' % (nightly_repo),
                        '%s/javadoc' % (nightly_web))        
        page = page + """
        <tr>
        <td valign=\"top\">
        <a href=\"http://java.sun.com/j2se/javadoc/doccheck/index.html\">DocCheck</a>
        results:</td><td> """
        subdirs = os.listdir('%s/reports/javadoc' % (nightly_repo))
        subdirs.sort()
        count = 1
        for dir in subdirs:
            page = page+"""
            <a href=\"javadoc/%s\">%s</a> """ % (dir, dir)
            if count % per_line == 0: page = page + "<br>"
            count += 1
        page = page + "</td></tr>"
    else:
        page = page + """
        <tr>
        <td valign=\"top\">
        <a href=\"http://java.sun.com/j2se/javadoc/doccheck/index.html\">DocCheck</a> results:</td>
        <td bgcolor=\"#ea3f3f\"><b>FAILED</b></td> """
        if os.path.exists( os.path.join(nightly_dir, 'doccheck.log') ):
            shutil.copyfile(os.path.join(nightly_dir, 'doccheck.log'),
                            os.path.join(nightly_web, 'doccheck.log'))            
            page = page + """
            <td valign=\"top\">
            <a href=\"doccheck.log\">doccheck.log</a>
            </td></tr>
            """
        else: page = page + "</tr>"


        

    # get the results of the PMD analysis
    if successPMD:
        page = page + """
        <tr>
        <td valign=\"top\"><a href=\"http://pmd.sourceforge.net/\">PMD</a> results:</td><td> """
        
        # make the PMD dir in the web dir
        os.mkdir(os.path.join(nightly_web,'pmd'))

        # transform the PMD XML output to nice HTML
        xmlFiles = glob.glob(os.path.join(nightly_repo,'reports/pmd/*.xml'))
        xmlFiles.sort()
        count = 1
        for xmlFile in xmlFiles:
            prefix = os.path.basename(xmlFile).split('.')[0]
            htmlFile = os.path.join(nightly_web, 'pmd', prefix)+'.html'
            transformXML2HTML(xmlFile, htmlFile)
            page = page+"""<a href=\"pmd/%s\">%s</a> """ % (os.path.basename(htmlFile), prefix)
            if count % per_line == 0: page = page + "<br>"
            count += 1
        page = page + "</td></tr>"
    else: # PMD stage failed for some reason
        page = page + """
        <tr>
        <td valign=\"top\"><a href=\"http://pmd.sourceforge.net/\">PMD</a> results:</td>
        <td bgcolor=\"ea3f3f\"><b>FAILED</b></td>
        """
        if os.path.exists( os.path.join(nightly_dir, 'pmd.log') ):
            shutil.copyfile(os.path.join(nightly_dir, 'pmd.log'),
                            os.path.join(nightly_web, 'pmd.log'))            
            page = page + """
            <td valign=\"top\">
            <a href=\"pmd.log\">pmd.log</a>
            </td></tr>
            """
        else: page = page + "</tr>"        

    # try and run japitools
    page = generateJAPI(page)
        
    # copy this script to the nightly we dir. The script should be in nightly_dir
    shutil.copy( os.path.join(nightly_dir,'nightly.py'), nightly_web)

    # close up the HTML and write out the web page
    writeNightlyPage(page)
             
    # go back to where we started
    os.chdir(start_dir)

    sys.exit(0)
