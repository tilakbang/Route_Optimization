from django.http.response import HttpResponse
from django.shortcuts import render
import pandas as pd
from geopy.distance import geodesic
from math import ceil
import requests
# Create your views here.
params={}

def index(request):
    return render(request, 'index.html')

def excelinput(request):
    if request.method=="POST":
        capacity = int(request.POST['capacity'])
        lat = float(request.POST['lat'])
        long = float(request.POST['long'])
        option = int(request.POST['format'])
        uploaded_file=request.FILES['document']
        # print(option, type(option))
        if option==1:
            main_1(capacity,lat,long,uploaded_file)
        elif option==2:
            main_2(capacity,lat,long,uploaded_file)
        return render(request, 'nextpage.html', params)
    else:
        return HttpResponse("invalid")  

def clustering(capicity, df):
    # df = pd.read_excel("D:\\SY CS\\EDI\\Book2.xlsx", "Sheet1")
    lat = list(df["Latitude"])
    long = list(df["Longitude"])
    load = list(df["load"])
    cord = {(lat[i], long[i]): load[i] for i in range(len(lat))}
    # capicity = int(input("Enter capicity of vechicle :"))
    del_cords=[]
    for i in cord:
        if cord[i]>capicity:
            # print("The load at the point "+str(i)+" is greater than capicity so this point will not be included in any of the clusters")
            del_cords.append(i)
    params['msg']=del_cords
    for i in del_cords:
        del cord[i]
            
    cluster = ceil(sum(load) / capicity)
    all_include=True
    clusters={}
    while(all_include):
        count = 0
        centroid = []
        for i in cord:
            centroid.append(i)
            count += 1
            if (count == cluster):
                break
        clusters={i:[] for i in centroid}
        for z in range(2):
            for i in cord:
                ref_dic = {}
                centroid = list(clusters.keys())
                for j in centroid:
                    ref_dic[float(geodesic(i, j).km)] = (i, j)
                l = list(sorted(ref_dic))
                ref_dic = {i: ref_dic[i] for i in l}
                l1 = ref_dic.values()
                for k in l1:
                    ref_list = [cord[i] for i in clusters[k[1]]]
                    total = sum(ref_list) + cord[i]
                    c = k[1]
                    li = clusters[c]
                    del clusters[c]
                    newlat = (c[0] + i[0]) / 2
                    newlong = (c[1] + i[1]) / 2
                    clusters[(newlat, newlong)] = li
                    clusters[(newlat, newlong)].append(i)
                    break
            new_centroid=[]
            for i in clusters:
                min=geodesic(i,clusters[i][0]).km
                n_c=clusters[i][0]
                for j in clusters[i]:
                    temp=geodesic(i,j).km
                    if temp>min:
                        min=temp
                        n_c=j
                new_centroid.append(n_c)
            clusters={i:[] for i in new_centroid}
        for i in cord:
            ref_dic = {}
            centroid = list(clusters.keys())
            for j in centroid:
                ref_dic[float(geodesic(i, j).km)] = (i, j)
            l = list(sorted(ref_dic))
            ref_dic = {i: ref_dic[i] for i in l}
            l1 = ref_dic.values()
            for k in l1:
                ref_list = [cord[i] for i in clusters[k[1]]]
                total = sum(ref_list) + cord[i]
                if (total <= capicity):
                    c = k[1]
                    li = clusters[c]
                    del clusters[c]
                    newlat = (c[0] + i[0]) / 2
                    newlong = (c[1] + i[1]) / 2
                    clusters[(newlat, newlong)] = li
                    clusters[(newlat, newlong)].append(i)
                    break
        total_points=0
        for i in clusters:
            total_points+=len(clusters[i])
        if len(cord)==total_points:
            all_include=False
        else:
            cluster+=1
            print(cluster)
    return clusters


def two_opt_2(route):
    best = route
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route) - 1):
            for j in range(i + 1, len(route)):
                if j - i == 1: continue  # changes nothing, skip then
                new_route = route[:]
                new_route[i:j] = route[j - 1:i - 1:-1]  # this is the 2woptSwap
                if route_dist_2(new_route) < route_dist_2(best):  # what should cost be?
                    best = new_route
                    improved = True
        route = best
    return best

def two_opt(route):
    ref_list=route.copy()
    ref_list.pop()
    distance_dic={}
    for i in range(len(ref_list)):
        distance_dic[(ref_list[i],ref_list[i])]=0
        for j in range(i+1,len(ref_list)):
            # distance_dic[(ref_list[i],ref_list[j])]=geodesic(ref_list[i],ref_list[j]).km
            distance_dic[(ref_list[i], ref_list[j])] =apiroute(ref_list[i],ref_list[j])
            # print(distance_dic[(ref_list[i], ref_list[j])])
            # distance_dic[(ref_list[j],ref_list[i])]=distance_dic[(ref_list[i],ref_list[j])]
            distance_dic[(ref_list[j], ref_list[i])] = distance_dic[(ref_list[i], ref_list[j])]
    best = route
    improved = True
    while improved:
        improved = False
        for i in range(1, len(route) - 1):
            for j in range(i + 1, len(route)):
                if j - i == 1: continue  # changes nothing, skip then
                new_route = route[:]
                new_route[i:j] = route[j - 1:i - 1:-1]  # this is the 2woptSwap
                if route_dist(new_route,distance_dic) < route_dist(best,distance_dic):  # what should cost be?
                    best = new_route
                    improved = True
        route = best
    return (best,route_dist(best,distance_dic))

def secondmin(dic):
    dist=list(sorted(dic.values()))
    for i in dic:
        if dic[i]==dist[1]:
            return i


def second_min(dic,minimal):
    ref_set={j for i in minimal for j in i}
    
    # ref_set={i for i in ref_dic if ref_dic[i] in ref_set}
    dist_dic={k for i in ref_set for k in dic if k[0]==i}
    dist_dic={k:geodesic(k[0],k[1]).km for k in dist_dic}
    sorted_values = sorted(dist_dic.values())  # Sort the values
    sorted_dict = {}
    for i in sorted_values:
        for k in dist_dic.keys():
            if dist_dic[k] == i:
                sorted_dict[k] = dist_dic[k]
    for i in sorted_dict:
        if i[0]!=i[1] and i not in minimal and  i[1] not in ref_set:
            return i


def minimum_spanning_tree(cluster):
    # print(len(cluster))
    minimal_spanning=[]
    dist_dic={(cluster[0],cluster[i]):geodesic(cluster[0],cluster[i]).km for i in range(0,len(cluster))}
    minimal_spanning.append(secondmin(dist_dic))
    dist_dic={(i,j):geodesic(i,j).km for i in cluster for j in cluster}
    # print(minimal_spanning)
    for i in range(len(cluster)-2):
        minimal_spanning.append(second_min(dist_dic, minimal_spanning))
    return minimal_spanning


def just_route(minimum_spanning_tree,starting_point):
    # starting_point = (18.6025509, 74.0047135)
    l=[]
    for i in minimum_spanning_tree:
        if i[0] not in l:
            l.append(i[0])
    max_dist = geodesic(l[0], starting_point).km
    last_point=l[0]
    for i in l:
        temp = geodesic(starting_point, i).km
        if temp > max_dist:
            max_dist = temp
            last_point = i
    m = (starting_point[1] - last_point[1]) / (starting_point[0] - last_point[0])
    c = starting_point[1] - m * starting_point[0]
    l=[]
    for i in minimum_spanning_tree:
        for j in i:
            if j not in l:
                l.append(j)
    l.remove(starting_point)
    l1 = []
    l2 = []
    for i in l:
        value = i[1] - m * i[0] - c
        if value > 0:
            l1.append(i)
        else:
            l2.append(i)
    l1.insert(0, starting_point)
    l2.insert(0, starting_point)
    for i in range(len(l2)):
        l1.append(l2[-1])
        l2.remove(l2[-1])
    return l1


def route_dist(l,distance_dic):
    dist=0
    for i in range(len(l)-1):
        dist=dist+distance_dic[(l[i],l[i+1])]
    return dist

def route_dist_2(l):
    dist=0
    for i in range(len(l)-1):
        dist=dist+geodesic(l[i],l[i+1]).km
    return dist

def apiroute(c1,c2):
    key = 'Al7q1kp7YP-UbS2gM6u7R1sXtXgnH0rWBc_s_r17qnSCndLXvHepYOouw6BmPqyO'
    firstVal = "https://dev.virtualearth.net/REST/v1/Routes/DistanceMatrix?origins="
    secondVal = "&destinations="
    start = str(c1[0])+','+str(c1[1])
    end = str(c2[0])+','+str(c2[1])
    lastVal = "&travelMode=driving&key=" + key
    url = firstVal + start + secondVal + end + lastVal
    output = requests.get(url).json()
    dis=float(output['resourceSets'][0]['resources'][0]['results'][0]['travelDistance'])
    return dis


def main_1(capacity, lat, long, uploaded_file):
    starting_point=(lat, long)
    df = pd.read_excel(uploaded_file, "Sheet1")
    clusters=clustering(capacity, df)
    lat = list(df["Latitude"])
    long = list(df["Longitude"])
    indexinexcel = {(lat[i], long[i]): (i+1) for i in range(len(lat))}
    indexinexcel[starting_point]=0
    urllist=[]
    total=0
    routes=[]
    ind_route_distance=[]
    for i in clusters:
        if len(clusters[i])!=1:
            cluster=clusters[i].copy()
            cluster.insert(0,starting_point)
            minimumspanningtree=minimum_spanning_tree(cluster)
            l=just_route(minimumspanningtree,starting_point)
            final_route_distance=two_opt(l)
            total+=final_route_distance[1]
            routes.append(indexing(indexinexcel,final_route_distance[0]))
            url=printurl(final_route_distance[0])
            urllist.append(url)
            # print(final_route_distance[0])
            # print(final_route_distance[1])
            ind_route_distance.append(final_route_distance[1])
        else:
            print(i)
    params['all']=[(routes[i],urllist[i],ind_route_distance[i]) for i in range(len(urllist))]
    params['totaldistance']=str(total)
    print('Total route distance is :'+str(total))

def main_2(capacity, lat, long, uploaded_file):
    starting_point=(lat, long)
    df = pd.read_excel(uploaded_file, "Sheet1")
    clusters=clustering(capacity, df)
    lat = list(df["Latitude"])
    long = list(df["Longitude"])
    indexinexcel = {(lat[i], long[i]): (i+1) for i in range(len(lat))}
    indexinexcel[starting_point]=0
    urllist=[]
    total=0
    routes=[]
    ind_route_distance=[]
    for i in clusters:
        if len(clusters[i])!=1:
            cluster=clusters[i].copy()
            cluster.insert(0,starting_point)
            minimumspanningtree=minimum_spanning_tree(cluster)
            l=just_route(minimumspanningtree,starting_point)
            route=two_opt_2(l)
            # plotting(route,a)
            url=printurl(route)
            urllist.append(url)
            total+=route_dist_2(route)
            # print(route)
            # print(indexing(indexinexcel,route))
            routes.append(indexing(indexinexcel,route))
            # print(route_dist_2(route))
            ind_route_distance.append(route_dist_2(route))
        else:
            print(i)
    params['all']=[(routes[i],urllist[i],ind_route_distance[i]) for i in range(len(urllist))]
    params['totaldistance']=str(total)
    print('Total route distance is :'+str(total))

def printurl(route):
    url1="https://dev.virtualearth.net/REST/v1/Imagery/Map/Road/Routes?"
    key = 'Al7q1kp7YP-UbS2gM6u7R1sXtXgnH0rWBc_s_r17qnSCndLXvHepYOouw6BmPqyO'
    for i in range(len(route)):
        url1+="wp."+str(i)+"="+str(route[i][0])+','+str(route[i][1])+';66;'+str(i+1)+'&'
    url=url1+'key='+key
    return url

def indexing(indexinexcel,route):
    l=""
    for i in route:
        l+=str(indexinexcel[i])+" => "
    l=l[:-3]
    return l
