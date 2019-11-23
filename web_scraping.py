%reset -f
import pandas as pd
from bs4 import BeautifulSoup
import numpy as np
import urllib.request
import urllib3

################################ Attributions #########################################

# https://towardsdatascience.com/value-investing-dashboard-with-python-beautiful-soup-and-dash-python-43002f6a97ca
# https://www.codeproject.com/Articles/1227268/Accessing-Financial-Reports-in-the-EDGAR-Database
# "Python and Web Data Extraction: Introduction" by Alvin Zuyin Zheng
# "Scraping EDGAR with Python" by Rasha Ashraf, Journal of Education for Business
# https://stackoverflow.com/questions/47736600/how-to-get-a-value-from-a-text-document-that-has-an-unstructured-table
# https://stackoverflow.com/questions/2010481/how-do-you-get-all-the-rows-from-a-particular-table-using-beautifulsoup
# https://www.youtube.com/watch?v=gfpmKkxhb9M
# https://www.youtube.com/watch?v=XQgXKtPSzUI
# Conversations with Brandon Checchi
# "Pandas for Everyone: Python Data Analysis" by Daniel Y. Chen
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
# "Python for Data Analysis" by Wes McKinney
# "Python Data Science Handbook" by Jake VanderPlas
# "Think Python" by Allen B. Downey
# https://realpython.com/

############################### Attributions ##########################################


# link to FCCY's 12/31/2017 10-K in html format.
# https://www.sec.gov/ix?doc=/Archives/edgar/data/1141807/000114180718000005/fccy-20171231x10k.htm

# link to all edgar filings
# https://www.sec.gov/Archives/edgar/full-index/
# select a year, then quarter, then master.idx which you will open with a text editor.
# you can see there are various filings (10-K, 10-Q, ). Iterating through each of these fillings can also be automated.


pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)

# If you want to redownload then use the link below
u = urllib.request.urlopen('https://www.sec.gov/Archives/edgar/data/1141807/000114180718000005/0001141807-18-000005.txt')

soup = BeautifulSoup(u, 'html.parser')

# find all tables in the document, one of which is the Balance Sheet.
soup.find_all('table')
tables= soup.find_all('table')

len(tables)
# Per visual inspection of the 10-K, the Balance Sheet has "ASSETS" written in all caps. Find the table or tables that have "ASSETS"
marker=0
for i,j in enumerate(tables):
    # turn each table into a string
    str= j.text
    # find this tile in part of the string
    if str.find('ASSETS') != -1:
        marker= i

marker

# Per above, it is the 104th table that is the balance sheet. Remember that Python indices start at 0.

# Below, look at the nested tags, etc.
print(tables[marker].prettify())

# get a count of all td items per row. This will provide a row count, a td count within each row, and the text of the td item.
for i,j in enumerate(tables[marker].find_all('tr')):
    for b,c in enumerate(j.find_all('td')):
        print(i, b, c.text)

# Use the above template to create a new dataframe with columns for i, b, and c.text.
d=[]
for i,j in enumerate(tables[marker].find_all('tr')):
    for b,c in enumerate(j.find_all('td')):
        d.append({'Row' : i, 'Cell': b, 'Balance': c.text})

d
df= pd.DataFrame(d)

df

# Go through and clean out td items that are throwing the table off. The goal is to have each financial statement line item followed by each of the two years on the balance sheet.
df= df.drop(df[df['Balance'] == "$"].index)
df= df.drop(df[df['Balance'] == ")"].index)
df= df.drop(df[df['Balance'] == "("].index)
df= df.drop(df[df['Balance'] == ""].index)

df

# The above is closer to the desired result, but there still appear to be rows with null values. Manually display what appear to be missing rows.
df['Balance'][9]

# Rows that appear to be missing contain '\xa0'. Drop these phantom rows.
df= df.drop(df[df['Balance'] == "\xa0"].index)

df

# Calculate the sum of the cell values for each individual item in row using "groupby". Next, drop all sums that are equal to zero since these are for line items in the Balance Sheet without financial statement numbers (e.g., headings, etc. )
df['sum']=df.groupby('Row')['Cell'].transform('sum')
df['sum'].describe()
df
df= df.drop(df[df['sum'] == 0].index)
df['sum'].describe()
# Per the above, the min is now 4, so the rows witout multiple cells are now removed (i.e., all rows that are just titles, etc.)
df.drop(['sum'], axis=1, inplace=True)
df.head(11)

# Every cell equal to 0 is the title of a Balance Sheet account, the next positive number for cell is the current year balance, and the maximum number for cell is the prior year balance. Need to deal with negative numbers which have that ( opening parenthese later. Create three columns, one for the title of each account on the Balance Sheet, one for the current year balance, and one for the prior year balance. Each column will be pulled into a DataFrame later.

%whos

col1=[]
col2=[]
col3=[]
df
# reset the index to be equal to the obs/row number.
df.reset_index(inplace=True, drop=True)
df.head()

df

# Start at the 2nd element and iterate by 3 for Balance Sheet account titles.
for i in range(2, (len(df)-2),3):
    col1.append(df['Balance'].loc[i])

col1

# start at the third element and iterate by 3 for current year balances (2017).
for i in range(3, (len(df)-1), 3):
    col2.append(df['Balance'].loc[i])

col2

# start at the fourth element and iterate by 3 for the prior year balances (2016)
for i in range(4, len(df), 3):
    col3.append(df['Balance'].loc[i])

col3

# create a list object with each of the above columns.
listoflists= [col1, col2, col3]
# create a dataframe from the listoflists object.
df4= pd.DataFrame(listoflists)
df4

# Need to bring in a composite index "cik, year" to put in rows 1 and 2.
# cik, 0 from df
# cik, 1 from df.

# feed in the link to the html file, which includes the cik for the firm. The ability to pull the cik into the DataFrame is important if this process is to be automated. For example, iterate through the list of EDGAR filings, pull each 10-K, webscrape data for each firm's Balance Sheet. The code here would need to be modified for other firms if they do not all have "ASSETS" in caps on their balance sheets. Additionally, there is a large amount of variation in balance sheet account titles for various firms. This would also need to be dealt with later to make sure that firms that report "Cash" vs., say, "Cash and Cash Equivalents" etc. are all combined into one variable with just Cash.
url=('https://www.sec.gov/Archives/edgar/data/1141807/000114180718000005/0001141807-18-000005.txt')
start= 'https://www.sec.gov/Archives/edgar/data/'
# remove above then keep everything until / and that will be the cik.
url2= url.replace(start,'')
url2
sep= '/'
# split on seperator one time, and keep the fist element.

cik= url2.split(sep)[0]
cik

df4.head()
last= len(df4.columns)
last

# since Python starts at the 0th index, the length of the columns is equal to the next column I want to create. I don't want to reset the column indices now because this could cause problems with the automated scrape later.
df4[last]= int(cik)
df4.head()

df4.loc[0, last] = 'cik'
df4.head()
df4[last+1]= np.nan
df4.head()

df4.loc[0, last+1]= 'year'
df4
df['Balance']
df4.loc[1, last+1]= df['Balance'][0]
df4.loc[2, last+1]= df['Balance'][1]
df4.head()

df4
df4.loc[0]

# replace the column index, which is currently numeric, with the first row which contains the balance sheet account titles.
df4.columns= df4.loc[0]

df4
# drop the row 0th row since the account names are now in the index.
df4.drop(df4.index[0], inplace=True)
df4

df4.set_index(['cik', 'year'], inplace=True)
df4

df4
df4.info()

# Next, convert the strings into integers. Per visual inspection, need to deal with three issues 1) leading ( for negative numbers, 2) pulling commas out of each string and 3) — for values of 0.
df4=df4.apply(lambda x: x.str.replace('(', '-'))
df4= df4.apply(lambda x: x.str.replace(',', ''))
df4
# can see above that variables with 0 values have a dash-type character.
df4['Other Real Estate Owned'].value_counts()
df4= df4.apply(lambda x: x.str.replace('—', '0'))
df4
# Convert strings to integers
df4= df4.apply(lambda x: pd.to_numeric(x))
df4
df4.info()

# Look at two examples.
df4['Interest-earning deposits'].describe()
# note below that loans has a trailing space. Need to strip these.
df4['Loans '].describe()
