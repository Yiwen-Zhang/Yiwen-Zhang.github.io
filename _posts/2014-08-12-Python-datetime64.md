---
layout: post
title: Have Fun with Timestamp
tag:
- python
---


Pandas time stamp uses the NumPy datetime64 dtype.

Convert epoch time into timestamp:


	pd.to_datetime(df.pixts/1000, unit='s', utc=True)

Convert time into date, hour, weekdays:

	df['dd'] = df.dt.apply(lambda x: pd.datetime.date(x))
	df['hh'] = df.dt.copy().apply(lambda x: x.hour)
	df['wd'] = df.dt.apply(lambda x: x.weekday())

The null values in timestamp is NaT.  The un-null value is always >= the null value. 
Find out null values:

	df.dt.isnull()
