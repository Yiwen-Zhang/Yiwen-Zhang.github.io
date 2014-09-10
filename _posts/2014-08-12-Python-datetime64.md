---
layout: post
title: Have Fun with Timestamp
tag:
- python
---


Timestamps always give me a headache.  My old trick of converting everything into character strings, and stripping out each time component is not very efficient.  Since we are in this business, we are gonna do it right.  Here is everything I learnt about timestamp. 

### Character date string

It is common that the dataset has a column called date with format ```dd-mm-yyyy```.  If the data is kept in a numpy dataframe, it can be converted into timestamp easily.  

	ts = df.datestring.astype('datetime64[D]')

Now, all the operations on timestamp is avalable to the variable ```ts```.  
	
	
### Epoch time

My favorite timestamp.  By definition epoch time is the number of seconds that have elapsed since January 1, 1970 (midnight UTC/GMT), not counting leap seconds (in ISO 8601: 1970-01-01T00:00:00Z).  Sometimes epoch time is stored in milliseconds or nanoseconds.  In cases that operations need to be done on timestamp, keeping everything in epoch time is the fastest I've ever seen, because they are just operations on integers.  

To get the epoch time of 00:00 on the last day in ```ts```:
	
	lastDay = np.datetime64( ts.max(), 's' ).astype(int)
	
The function ```np.datetime64()``` is not vectorized.  Note that this will return the 00:00 in UTC time on the last day.  In order to get the local 00:00, we need to take that 'lastDay', and add the offset (in seconds).  

	lastDayLocal = lastDay + offset

It would be nice if the data frame has a vector of epoch timestamp ('ets') recording the actual time point.

We are able to round off the epoch seconds to hours, days, and etc. 

	df['hour'] = df.ets.values.astype('datetime64[s]').astype('datetime[h]')
	df['date'] = df.ets.values.astype('datetime64[s]').astype('datetime[D]')

To get the time of the day the event happens, we can perform the numerical operations on the timestamps.  Note that the results are in nanoseconds. 

	df['hh'] = df.hour.values - df.dd.values
	df['hh'] = df.hh.astype(int)/3.6e12
	

### Null values in time 

The null values in timestamp is ```NaT```.  The un-null value is always $$\geq$$ the null value. Find out null values:

	df.dt.isnull()	

### Other stuff

Other ways to convert epoch time into human readable timestamp:

	pd.to_datetime(df.pixts/1000, unit='s', utc=True)

Do avoid using apply to convert time into date, hour, weekdays.  The following code is insanely slow!

	df['dd'] = df.dt.apply(lambda x: pd.datetime.date(x))
	df['hh'] = df.dt.copy().apply(lambda x: x.hour)
	df['wd'] = df.dt.apply(lambda x: x.weekday())


