from pyspark import SparkContext
import time


#Pre-Processing - multi line value
def multi2single(path):

	data = sc.textFile(path).collect()[:]

	temp = []

	for d in data:

		if len(d) > 1:
			try:
				temp.append(str(d).replace('\x00',''))
			except:
				temp.append(str(d.encode('utf8')).replace('\x00',''))
	
	ind = 0
	while(True):
		if ind == len(temp):
			break
		if len(temp[ind]) >= 1 and str(temp[ind])[-1] == '\\':
			temp[ind] = temp[ind][:-1]+temp[ind+1][2:]
			del temp[ind+1]
		else:
			ind += 1

	return temp



#Pre-Processing
def mk_unit(path):

	sample = multi2single(path)

	data = []

	ind = 0
	while(True):

		if ind >= len(sample):
			break

		if str(sample[ind])[0] == '[':

			temp = [str(sample[ind])]
			k = ind+1

			while(True):
				if k >= len(sample) or sample[k][0] == '[':
					break
				else:
					temp.append(str(sample[k]))
					k += 1
			
			data.append(temp)
			ind = k
		else:
			ind += 1

	result = []

	for d in data:
		if len(d) == 1:
			result.append(d[0][1:-1])
		else:
			for ind in range(1, len(d)):
				result.append(d[0][1:-1]+'\\'+d[ind])

	return result



#save as key-value
def reg2dict(data):

	if '=' in data:
		value_name = 'default' if data.split('=')[0].split('\\')[-1] == '@' else data.split('=')[0].split('\\')[-1][1:-1]
		value_data = data.split('=')[1] if str(data.split('=')[1])[0] != '"' else data.split('=')[1][1:-1]
		values = [{value_name : value_data}]
		keys = data.split('=')[0].split('\\')[:-1]
	else:
		values = [{}]
		keys = data.split('\\')
	
	key_value = keys+values

	for i in range(len(key_value)-2,-1,-1):
		key_value[i] = { key_value[i] : key_value[i+1] }

	return key_value[0]

	
#reduce

x = {'HKCC' : {'System' : {'CurrentA' : 'control'}}}
y = {'HKCC' : {'System' : {'CurrentB' : 'setting'}}}

def dict_reduce(x,y):

	keys = []
	
	check = 0

	while(True):
		if list(x.values())[0].keys() != list(y.values())[0].keys():
			keys.append(list(x.keys())[0])
			if list(list(y.values())[0].keys())[0] in list(list(x.values())[0].keys()):
				check = 1
			break
		else:
			keys.append(list(x.keys())[0])
			x = list(x.values())[0]
			y = list(y.values())[0]

	if check == 1:
		x.values()[0][y.values()[0].keys()[0]].update(y.values()[0].values()[0])
	else:
		list(x.values())[0].update(list(y.values())[0])

	result = list(x.values())[0]

	for ind in range(len(keys)-1,-1,-1):

		result = {keys[ind] : result}

	return result

	
def final_index(data):

	ind = 0
	for i in range(len(data)-1,-1,-1):
		if str(data[i]) == ':':
			ind = i
			break

	return len(data)-ind
	



if __name__ == "__main__":

	#setting
	sc = SparkContext()
	path = "gs://dataproc-staging-asia-east1-804846661812-k5oy6idn/"
	keyword = 'sys'
	
	start_time = time.time()

	# #map
	map_data = sc.parallelize(mk_unit(path+'test.reg')).flatMap(lambda x : x.split('/n')).map(lambda x : reg2dict(x))#.reduce(lambda x,y : dict_reduce(x,y)).repartition(8)
	# sc.parallelize(map_data).saveAsTextFile(path+'result')
	map_data.saveAsTextFile(path+'result')

	finish_time = time.time()


	print("Time : "+str(finish_time - start_time))


	# final_data = sc.textFile(path+"result/*").repartition(partition_size)
	# start_time = time.time()

	# # registry key search
	# data = final_data.filter(lambda x : keyword in x[:final_index(x)])#.map(lambda x : eval(x)).reduce(lambda x,y : dict_reduce(x,y))

	# finish_time = time.time()
	# print("Number of Partition : "+str(final_data.getNumPartitions())+"    Time : "+str(finish_time - start_time)+"    Result : "+str(len(data.collect())))


