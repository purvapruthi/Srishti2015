import urllib2
from urlparse import urlparse
from BeautifulSoup import *
from urlparse import urljoin
from pysqlite2 import dbapi2 as sqlite
import csv

# Create a list of words to ignore
ignorewords={'the':1,'of':1,'to':1,'and':1,'a':1,'in':1,'is':1,'it':1,'\n':1}

class crawler:
  # Initialize the crawler with the name of database
  def __init__(self,dbname):
    self.con=sqlite.connect(dbname)
    self.con.text_factory = str
  
  def __del__(self):
    self.con.close()

  def dbcommit(self):
    self.con.commit()

  # Auxilliary function for getting an entry id and adding 
  # it if it's not present
  def getentryid_url(self,table,field1,field2,value1,value2,createnew=True):
    cur=self.con.execute(
    "select rowid from %s where %s='%s'" % (table,field2,value2))
    res=cur.fetchone()
    if res==None:
      cur=self.con.execute(
      "insert into %s (%s,%s) values ('%s','%s')" % (table,field1,field2,value1,value2))
      return cur.lastrowid
    else:
      return res[0] 

  def getentryid_word(self,table,field,value,createnew=True):
    cur=self.con.execute(
    "select rowid from %s where %s='%s'" % (table,field,value))
    res=cur.fetchone()
    if res==None:
      cur=self.con.execute(
      "insert into %s (%s) values ('%s')" % (table,field,value))
      return cur.lastrowid
    else:
      return res[0] 

  


  # Index an individual news
  def addtoindex(self,newsid,url,soup):
    if self.isindexed(url): return
    print newsid
    # Get the individual words
    words=self.separatewords(soup.lower())
    
   
    # Get the URL id
    news_id=self.getentryid_url('urllist','newsid','url',newsid,url)
   
    
    # Link each word to this newsid
    for i in range(len(words)):
      word=words[i]
      if word in ignorewords: continue
      wordid=self.getentryid_word('wordlist','word',word)
      
      self.con.execute("insert into wordlocation(urlid,wordid,location) values (%d,%d,%d)" % (news_id,wordid,i))
  

  # Seperate the words by any non-whitespace character
  def separatewords(self,text):
    splitter=re.compile('\\W*')
    return [s.lower() for s in splitter.split(text) if s!='']
  
 # Return true if this url is already indexed
  def isindexed(self,url):
    u=self.con.execute("select rowid from urllist where url='%s'" % url).fetchone()
    if u!=None:
      return True
    return False

 
   
  def importdata(self,csvfile):
    newsitems = csv.reader(open(csvfile))
    self.con.executemany("insert into newslist values (?, ? ,? ,? ,? ,? )",newsitems)
          
  
 
  # Create the database tables
  def createindextables(self): 
    self.con.execute('create table newslist(newsid INTEGER PRIMARY KEY,headline,startdate,enddate,source int ,newsurl)')
    self.con.execute('create table urllist(newsid,url,FOREIGN KEY(newsid) REFERENCES newslist(newsid) )')
    self.con.execute('create table wordlist(word)')
    self.con.execute('create table domainname(source int ,domain)')
    self.con.execute('create table wordlocation(urlid,wordid,location)')
    self.con.execute('create index urlidx on urllist(url)')
    self.con.execute('create index wordidx on wordlist(word)')
    self.con.execute('create index newsidx on newslist(newsid)')
    self.con.execute('create index wordnewsidx on wordlocation(wordid)')
    
    self.dbcommit()
   
  def indexurl(self):
   for (newsid,headline,source,newsurl,) in self.con.execute("select newsid,headline,source,newsurl from newslist "):
      if newsurl[0:4]!='http':
        wordrow=self.con.execute("select domain from domainname where source = %d" % source).fetchone()
        if wordrow == None:
          for (url,) in self.con.execute('select newsurl from newslist where source=%d ' % source):
            if url[0:4] == 'http':
	      parsed_uri = urlparse(url)
              domain = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
	      self.con.execute("insert into domainname(source,domain) values('{0}','{1}')" .format(int (source),domain))
	      url = domain+""+newsurl
              break
        else:
          for (domainvalue,) in self.con.execute("select domain from domainname where source= %d" % source):
            url = domainvalue+""+newsurl
      else:
       url = newsurl
      try:
        soup=headline
        self.addtoindex(newsid,url,soup)           
	self.dbcommit()
      except:
          print "Could not parse url %s" % url

   print "Indexing Complete"

   
    
            
         
  
class searcher:
  def __init__(self,dbname):
    self.con=sqlite.connect(dbname)

  def __del__(self):
    self.con.close()

  def getmatchrows(self,q):
    # Strings to build the query
    fieldlist='w0.urlid'
    tablelist=''  
    clauselist=''
    wordids=[]

    # Split the words by spaces
    q=q.lower()
    words=q.split(' ')  
    tablenumber=0

    for word in words:
      # Get the word ID
      wordrow=self.con.execute(
      "select rowid from wordlist where word='%s'" % word).fetchone()
      
      if wordrow!=None:
        wordid=wordrow[0]
        
        wordids.append(wordid)
        if tablenumber>0:
          tablelist+=','
          clauselist+=' and '
          clauselist+='w%d.urlid=w%d.urlid and ' % (tablenumber-1,tablenumber)
        fieldlist+=',w%d.location' % tablenumber
        tablelist+='wordlocation  w%d' % tablenumber      
        clauselist+='w%d.wordid=%d' % (tablenumber,wordid)
        tablenumber+=1
    

    # Create the query from the separate parts
    fullquery= "select %s from %s where %s" % (fieldlist,tablelist,clauselist)
    
    cur=self.con.execute(fullquery)
    rows=[row for row in cur]

    return rows,wordids

  def getscoredlist(self,rows,wordids):
    totalscores=dict([(row[0],0) for row in rows])

    # This is where we'll put our scoring functions
    weights=[(1.0,self.locationscore(rows)), 
             (1.0,self.frequencyscore(rows)),
	     (1.0,self.distancescore(rows))]
    for (weight,scores) in weights:
      for url in totalscores:
        totalscores[url]+=weight*scores[url]

    return totalscores

  def geturlname(self,id):
    return self.con.execute(
    "select url from urllist where rowid=%d" % id).fetchone()[0]

  def query(self,q):
     rows,wordids=self.getmatchrows(q)
     scores=self.getscoredlist(rows,wordids)
     rankedscores=[(score,url) for (url,score) in scores.items()]
     rankedscores.sort()
     rankedscores.reverse()
     print 'Score\t\t\tURL'
     for (score,urlid) in rankedscores[0:10]:
       print '%f\t%s' % (score,self.geturlname(urlid))
     return wordids,[r[1] for r in rankedscores[0:10]]
    


  def normalizescores(self,scores,smallIsBetter=0):
    vsmall=0.00001 # Avoid division by zero errors
    if smallIsBetter:
      minscore=min(scores.values())
      return dict([(u,float(minscore)/max(vsmall,l)) for (u,l) in scores.items()])
    else:
      maxscore=max(scores.values())
      if maxscore==0: maxscore=vsmall
      return dict([(u,float(c)/maxscore) for (u,c) in scores.items()])

  def frequencyscore(self,rows):
    counts=dict([(row[0],0) for row in rows])
    for row in rows: counts[row[0]]+=1
    return self.normalizescores(counts)

  def locationscore(self,rows):
    locations=dict([(row[0],1000000) for row in rows])
    for row in rows:
      loc=sum(row[1:])
      if loc<locations[row[0]]: locations[row[0]]=loc
    
    return self.normalizescores(locations,smallIsBetter=1)

  def distancescore(self,rows):
    # If there's only one word, everyone wins!
    if len(rows[0])<=2: return dict([(row[0],1.0) for row in rows])

    # Initialize the dictionary with large values
    mindistance=dict([(row[0],1000000) for row in rows])

    for row in rows:
      dist=sum([abs(row[i]-row[i-1]) for i in range(2,len(row))])
      if dist<mindistance[row[0]]: mindistance[row[0]]=dist
    return self.normalizescores(mindistance,smallIsBetter=1)
	
  def searchbydate(self,query):
    for rows in self.con.execute("select distinct u.url from urllist u,newslist n where n.startdate='%s'" % query):
      print rows

  def maxnewsid(self):
    return self.con.execute("select max(newsid) from urllist").fetchone()[0]
    
   

 
