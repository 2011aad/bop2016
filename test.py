########### Python 2.7 #############
import httplib, urllib, base64, json, copy

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': 'f7cc29509a8443c5b3a5e56b0e38b5a6',
}

params_dic = {
    # Request parameters
    'expr': 'Id=2140251882',
    'model': 'latest',
    'attributes': 'RId,Id,AA.AuId,AA.AfId,F.FId,J.JId,C.CId',
    'count': '200',
    'offset': '0',
}

def wrapReq(ex, k, it):
    if len(ex)==0:
        if k=='Id':
            ex = 'Id=' + str(it)
        else:
            ex = 'Composite(' + k + '=' + str(it) + ')'
    else:
        if k=='Id':
            ex = 'Or(Id=' + str(it) + ',' + ex + ')'
        else:
            ex = 'Or(Composite(' + k + '=' + str(it) + '),' + ex + ')'

    return ex

def calPath(ps, s, d):
    results = []
    if d in ps.get(s):
        results.append([s,d])

    for m1 in ps.get(s):
        if ps.has_key(m1):
            if d in ps.get(m1):
                results.append([s,m1,d])

            for m2 in ps.get(m1):
                if ps.has_key(m2):
                    if d in ps.get(m2):
                        results.append([s,m1,m2,d])

    return results




source = 2140251883
destination = 2142155589
MAX_REQ_NUM = 40

path = {source:[]}
responses = []
old_data = {'Id':[], 'J.JId':[], 'C.CId':[], 'F.FId':[], 'AA.AuId':[], 'AA.AfId':[]}
new_data = {'Id':[], 'J.JId':[], 'C.CId':[], 'F.FId':[], 'AA.AuId':[], 'AA.AfId':[]}

conn = httplib.HTTPSConnection('oxfordhk.azure-api.net')
params_dic['expr'] = 'Id=' + str(source)
params = urllib.urlencode(params_dic)
conn.request("GET", "/academic/v1.0/evaluate?%s" % params, "{body}", headers)
responses.append(json.loads(conn.getresponse().read()))
if not responses[0].get('entities')[0].has_key('AA'):
    new_data['AA.AuId'].append(source)
else:
    new_data['Id'].append(source)


for i in range(3):
    #Create requests
    num = 0
    responses = []
    counter = 0
    expr = ''
    for key in new_data.keys():
        for item in new_data.get(key):
            expr = wrapReq(expr, key, item)
            counter += 1
            if counter==MAX_REQ_NUM:
                params_dic['expr'] = expr
                num += 1
                p = urllib.urlencode(params_dic)
                conn.request("GET", "/academic/v1.0/evaluate?%s" % p, "{body}", headers)
                responses.append(json.loads(conn.getresponse().read()))
                counter = 0
                expr = ''
    if len(expr)>0:
        params_dic['expr'] = expr
        num += 1
        p = urllib.urlencode(params_dic)
        conn.request("GET", "/academic/v1.0/evaluate?%s" % p, "{body}", headers)
        responses.append(json.loads(conn.getresponse().read()))

    print num

    print "iteration: " + str(i)
    #print responses
    old_data = copy.deepcopy(new_data)
    new_data = {'Id':[], 'J.JId':[], 'C.CId':[], 'F.FId':[], 'AA.AuId':[], 'AA.AfId':[]}
    #handle responses
    for resp in responses:
        entities = resp.get('entities')
        for entity in entities:

            RIds = entity.get('RId')
            Id = entity.get('Id')
            AAs = entity.get('AA')
            Conf = entity.get('C')
            Journal = entity.get('J')
            Fields = entity.get('F')

            #from id
            if Id in old_data['Id']:
                if not path.has_key(Id):
                    path[Id] = []

                #to J.JId
                if Journal:
                    JId = Journal.get('JId')
                    if JId not in new_data.get('J.JId'):
                        new_data['J.JId'].append(JId)
                    if JId not in path[Id]:
                        path[Id].append(JId)
                #to F.FId
                if Fields:
                    for Field in Fields:
                        FId = Field.get('FId')
                        if FId not in new_data.get('F.FId'):
                            new_data['F.FId'].append(FId)
                        if FId not in path[Id]:
                            path[Id].append(FId)
                #to C.CId
                if Conf:
                    CId = Conf.get('CId')
                    if CId not in new_data.get('C.CId'):
                        new_data['C.CId'].append(CId)
                    if CId not in path[Id]:
                        path[Id].append(CId)
                #to refrence Id
                if RIds:
                    for RId in RIds:
                        if RId not in new_data.get('Id'):
                            new_data['Id'].append(RId)
                        if RId not in path[Id]:
                            path[Id].append(RId)
                #to AA.AuId
                if AAs:
                    for AA in AAs:
                        AuId = AA.get('AuId')
                        if AuId not in new_data.get('AA.AuId'):
                            new_data['AA.AuId'].append(AuId)
                        if AuId not in path[Id]:
                            path[Id].append(AuId)

            #from F.FId
            if Fields:
                for Field in Fields:
                    FId = Field.get('FId')
                    if FId in old_data['F.FId']:
                        if not path.has_key(FId):
                            path[FId] = []

                        #to id
                        if Id not in new_data.get('Id'):
                            new_data['Id'].append(Id)
                        if Id not in path[FId]:
                            path[FId].append(Id)

            #from C.CId
            if Conf:
                CId = Conf.get('CId')
                if CId in old_data['C.CId']:
                    if not path.has_key(CId):
                        path[CId] = []

                    #to id
                    if Id not in new_data.get('Id'):
                        new_data['Id'].append(Id)
                    if Id not in path[CId]:
                        path[CId].append(Id)

            #from J.JId
            if Journal:
                JId = Journal.get('JId')
                if JId in old_data['J.JId']:
                    if not path.has_key(JId):
                        path[JId] = []

                    #to id
                    if Id not in new_data.get('Id'):
                        new_data['Id'].append(Id)
                    if Id not in path[JId]:
                        path[JId].append(Id)

            #from AA.AuId
            if AAs:
                for AA in AAs:
                    AuId = AA.get('AuId')
                    if AuId in old_data['AA.AuId']:
                        if not path.has_key(AuId):
                            path[AuId] = []

                        #to Id
                        if Id not in new_data.get('Id'):
                            new_data['Id'].append(Id)
                        if Id not in path[AuId]:
                            path[AuId].append(Id)

                        #to AfId
                        for AAp in AAs:
                            if not AAp.has_key('AfId'):
                                continue
                            AfId = AAp.get('AfId')
                            if AfId not in new_data.get('AA.AfId'):
                                new_data['AA.AfId'].append(AfId)
                            if AfId not in path[AuId]:
                                path[AuId].append(AfId)

            #from AA.AfId
            if AAs:
                for AA in AAs:
                    if not AA.has_key('AfId'):
                        continue
                    AfId = AA.get('AfId')
                    if AfId in old_data['AA.AfId']:
                        if not path.has_key(AfId):
                            path[AfId] = []

                        #to AuId
                        for AAp in AAs:
                            AuId = AAp.get('AuId')
                            if AuId not in new_data.get('AA.AuId'):
                                new_data['AA.AuId'].append(AuId)
                            if AuId not in path[AfId]:
                                path[AfId].append(AuId)


#print path
print
print "Results:"
print calPath(path, source, destination)

conn.close()

####################################