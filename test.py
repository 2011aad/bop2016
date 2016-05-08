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
    'count': '1000',
    'offset': '0',
}

def sendREQ(expr):
    params_dic['expr'] = expr
    params = urllib.urlencode(params_dic)
    conn.request("GET", "/academic/v1.0/evaluate?%s" % params, "{body}", headers)
    return json.loads(conn.getresponse().read())


def wrapReq(ex, k, it, operator):
    if len(ex)==0:
        if k=='Id' or k=='RId':
            ex = k + '=' + str(it)
        else:
            ex = 'Composite(' + k + '=' + str(it) + ')'
    else:
        if k=='Id' or k=='RId':
            ex = operator + '(' + k + '=' + str(it) + ',' + ex + ')'
        else:
            ex = operator + '(Composite(' + k + '=' + str(it) + '),' + ex + ')'

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



source = 2123314761
destination = 1982462162
MAX_REQ_NUM = 40
start = 0     #start = 0 : start with id, 1 : start with AuId
end = 0       #end = 0 : end with id, 1 : end with AuId

conn = httplib.HTTPSConnection('oxfordhk.azure-api.net')
#determine start id or AuId
params_dic['expr'] = 'Id=' + str(source)
params = urllib.urlencode(params_dic)
conn.request("GET", "/academic/v1.0/evaluate?%s" % params, "{body}", headers)
response = json.loads(conn.getresponse().read())
if len(response.get('entities'))==0 or not response.get('entities')[0].has_key('AA'):
    start = 1
    #new_data['AA.AuId'].append(source)
else:
    start = 0
    #new_data['Id'].append(source)

#determine end id or AuId
params_dic['expr'] = 'Id=' + str(destination)
params = urllib.urlencode(params_dic)
conn.request("GET", "/academic/v1.0/evaluate?%s" % params, "{body}", headers)
response = json.loads(conn.getresponse().read())
if len(response.get('entities'))==0 or not response.get('entities')[0].has_key('AA'):
    end = 1
    #new_data['AA.AuId'].append(source)
else:
    end = 0
    #new_data['Id'].append(source)

result = []
#start with an Id
if start == 0:
    expr = ""
    expr = wrapReq(expr, 'Id', source, 'Or')
    response = sendREQ(expr)
    entity = response.get('entities')[0]

    RIds = entity.get('RId')
    Id = entity.get('Id')
    AAs = entity.get('AA')
    Conf = entity.get('C')
    Journal = entity.get('J')
    Fields = entity.get('F')

    #end with an Id
    if end == 0:
        #one jump
        if destination in RIds:
            result.append([source, destination])

        #two jumps
        #RIds in the middle
        expr = ""
        newEntities = []
        if RIds:
            counter = 0
            for RId in RIds:
                expr = wrapReq(expr, 'Id', RId, 'Or')
                counter += 1
                if counter == MAX_REQ_NUM:
                    expr = wrapReq(expr, 'RId', destination, 'And')

                    response = sendREQ(expr)
                    for e in response.get('entities'):
                        result.append([source,e.get('Id'),destination])
                    counter = 0
                    expr = ""

        if len(expr)>0:
            expr = wrapReq(expr, 'RId', destination, 'And')
            response = sendREQ(expr)
        for e in response.get('entities'):
            result.append([source,e.get('Id'),destination])

        #destination information
        #others in the middle
        expr = ""
        expr = wrapReq(expr, 'Id', destination, 'And')
        response = sendREQ(expr)
        destEntity = response.get('entities')[0]
        if destEntity.get('C'):
            if Conf and destEntity.get('C').get('CId') == Conf.get('CId'):
                result.append([source, Conf.get('CId'), destination])
        if destEntity.get('J'):
            if Journal and destEntity.get('J').get('JId') == Journal.get('JId'):
                result.append([source, Journal.get('JId'), destination])

        newFields = destEntity.get('F')
        if newFields:
            for nf in newFields:
                if Fields:
                    for f in Fields:
                        if nf.get('FId') == f.get('FId'):
                            result.append([source, f.get('FId'), destination])

        newAAs = destEntity.get('AA')
        if newAAs:
            for nau in newAAs:
                if AAs:
                    for au in AAs:
                        if nau.get('AuId') == au.get('AuId'):
                            result.append([source, au.get('AuId'), destination])


        #three jumps

        #first class (all ids)   bottle neck
        newEntities = []
        expr = ""
        if RIds:
            counter = 0
            for RId in RIds:
                expr = wrapReq(expr, 'Id', RId, 'Or')
                counter += 1
                if counter==MAX_REQ_NUM:
                    response = sendREQ(expr)
                    newEntities.extend(response.get('entities'))
                    counter = 0
                    expr = ""
            if len(expr)>0:
                response = sendREQ(expr)
                newEntities.extend(response.get('entities'))

            for nentity in newEntities:
                nRIds = nentity.get('RId')
                ncounter = 0
                nexpr = ""
                for nRId in nRIds:
                    nexpr = wrapReq(nexpr, 'Id', nRId, 'Or')
                    ncounter += 1
                    if ncounter == MAX_REQ_NUM:
                        nexpr = wrapReq(nexpr, 'RId', destination, 'And')
                        response = sendREQ(nexpr)
                        for e in response.get('entities'):
                            result.append([source, nentity.get('Id'), e.get('Id'), destination])
                        counter = 0
                        nexpr = ""

                if len(nexpr)>0:
                    nexpr = wrapReq(nexpr, 'RId', destination, 'And')
                    response = sendREQ(nexpr)
                    for e in response.get('entities'):
                        result.append([source, nentity.get('Id'), e.get('Id'), destination])

        #second class
        expr = ""
        newEntities = []
        if Fields:
            for f in Fields:
                expr = wrapReq(expr, 'F.FId', f.get('FId'), 'Or')
        if Conf:
            expr = wrapReq(expr, 'C.CId', Conf.get('CId'), 'Or')
        if Journal:
            expr = wrapReq(expr, 'J.JId', Journal.get('JId'), 'Or')
        if AAs:
            for au in AAs:
                expr = wrapReq(expr, 'AA.AuId', au.get('AuId'),'Or')

        expr = wrapReq(expr, 'RId', destination, 'And')

        response = sendREQ(expr)
        newEntities = response.get('entities')
        for newE in newEntities:
            if newE.get('C'):
                if Conf and newE.get('C').get('CId') == Conf.get('CId'):
                    result.append([source, Conf.get('CId'), newE.get('Id'), destination])
            if newE.get('J'):
                if Journal and newE.get('J').get('JId') == Journal.get('JId'):
                    result.append([source, Journal.get('JId'), newE.get('Id'), destination])

            newFields = newE.get('F')
            if newFields:
                for nf in newFields:
                    if Fields:
                        for f in Fields:
                            if nf.get('FId') == f.get('FId'):
                                result.append([source, f.get('FId'), newE.get('Id'), destination])

            newAAs = newE.get('AA')
            if newAAs:
                for nau in newAAs:
                    if AAs:
                        for au in AAs:
                            if nau.get('AuId') == au.get('AuId'):
                                result.append([source, au.get('AuId'), newE.get('Id'), destination])


        #third class
        dRIds = destEntity.get('RId')
        dId = destEntity.get('Id')
        dAAs = destEntity.get('AA')
        dConf = destEntity.get('C')
        dJournal = destEntity.get('J')
        dFields = destEntity.get('F')

        newEntities = []
        expr2 = ""
        if dFields:
            for df in dFields:
                expr2 = wrapReq(expr2, 'F.FId', df.get('FId'), 'Or')
        if dConf:
            expr2 = wrapReq(expr2, 'C.CId', dConf.get('CId'), 'Or')
        if dJournal:
            expr2 = wrapReq(expr2, 'J.JId', dJournal.get('JId'), 'Or')
        if dAAs:
            for dau in dAAs:
                expr2 = wrapReq(expr2, 'AA.AuId', dau.get('AuId'),'Or')

        expr1 = ""
        if RIds and len(expr2)>0:
            counter = 0
            for RId in RIds:
                expr1 = wrapReq(expr1, 'Id', RId, 'Or')
                counter += 1
                if counter == MAX_REQ_NUM - 10:
                    expr = 'And(' + expr1 + ',' + expr2 + ')'

                    response = sendREQ(expr)
                    newEntities.extend(response.get('entities'))
                    counter = 0
                    expr1 = ""

        if len(expr1)>0 and len(expr2)>0:
            expr = 'And(' + expr1 + ',' + expr2 + ')'

            response = sendREQ(expr)
            newEntities.extend(response.get('entities'))

        for newE in newEntities:
            if newE.get('C'):
                if dConf and newE.get('C').get('CId') == dConf.get('CId'):
                    result.append([source, newE.get('Id'), Conf.get('CId'), destination])
            if newE.get('J'):
                if dJournal and newE.get('J').get('JId') == dJournal.get('JId'):
                    result.append([source, newE.get('Id'), Journal.get('JId'), destination])

            newFields = newE.get('F')
            if newFields:
                for nf in newFields:
                    if dFields:
                        for df in dFields:
                            if nf.get('FId') == df.get('FId'):
                                result.append([source, newE.get('Id'), df.get('FId'), destination])

            newAAs = newE.get('AA')
            if newAAs:
                for nau in newAAs:
                    if dAAs:
                        for au in dAAs:
                            if nau.get('AuId') == dau.get('AuId'):
                                result.append([source, newE.get('Id'), dau.get('AuId'), destination])

    #end with an AuId
    else:
        #one jump
        if AAs:
            for AA in AAs:
                if AA.get('AuId')==destination:
                    result.append([source, destination])
                    break;

        #two jumps
        newEntities = []
        if RIds:
            counter = 0
            for RId in RIds:
                expr = wrapReq(expr, 'Id', RId, 'Or')
                counter += 1
                if counter == MAX_REQ_NUM:
                    expr = wrapReq(expr, 'AA.AuId', destination, 'And')

                    response = sendREQ(expr)
                    for e in response.get('entities'):
                        result.append([source,e.get('Id'),destination])
                    counter = 0
                    expr = ""
        if len(expr)>0:
            expr = wrapReq(expr, 'AA.AuId', destination, 'And')

            response = sendREQ(expr)
            newEntities.extend(response.get('entities'))
        for e in response.get('entities'):
            result.append([source,e.get('Id'),destination])

        #three jumps
        #last 4 cases
        expr = ""
        newEntities = []
        if Fields:
            for f in Fields:
                expr = wrapReq(expr, 'F.FId', f.get('FId'), 'Or')
        if Conf:
            expr = wrapReq(expr, 'C.CId', Conf.get('CId'), 'Or')
        if Journal:
            expr = wrapReq(expr, 'J.JId', Journal.get('JId'), 'Or')
        if AAs:
            for au in AAs:
                expr = wrapReq(expr, 'AA.AuId', au.get('AuId'),'Or')

        expr = wrapReq(expr, 'AA.AuId', destination, 'And')

        response = sendREQ(expr)
        newEntities = response.get('entities')
        for newE in newEntities:
            if newE.get('C'):
                if Conf and newE.get('C').get('CId') == Conf.get('CId'):
                    result.append([source, Conf.get('CId'), newE.get('Id'), destination])
            if newE.get('J'):
                if Journal and newE.get('J').get('JId') == Journal.get('JId'):
                    result.append([source, Journal.get('JId'), newE.get('Id'), destination])

            newFields = newE.get('F')
            if newFields:
                for nf in newFields:
                    if Fields:
                        for f in Fields:
                            if nf.get('FId') == f.get('FId'):
                                result.append([source, f.get('FId'), newE.get('Id'), destination])

            newAAs = newE.get('AA')
            if newAAs:
                for nau in newAAs:
                    if AAs:
                        for au in AAs:
                            if nau.get('AuId') == au.get('AuId'):
                                result.append([source, au.get('AuId'), newE.get('Id'), destination])

        #case 2  bottle neck
        newEntities = []
        expr = ""
        if RIds:
            counter = 0
            for RId in RIds:
                expr = wrapReq(expr, 'Id', RId, 'Or')
                counter += 1
                if counter==MAX_REQ_NUM:
                    response = sendREQ(expr)
                    newEntities.extend(response.get('entities'))
                    counter = 0
                    expr = ""
            if len(expr)>0:
                response = sendREQ(expr)
                newEntities.extend(response.get('entities'))

            for nentity in newEntities:
                nRIds = nentity.get('RId')
                ncounter = 0
                nexpr = ""
                for nRId in nRIds:
                    nexpr = wrapReq(nexpr, 'Id', nRId, 'Or')
                    ncounter += 1
                    if ncounter == MAX_REQ_NUM:
                        nexpr = wrapReq(nexpr, 'AA.AuId', destination, 'And')
                        response = sendREQ(nexpr)
                        for e in response.get('entities'):
                            result.append([source, nentity.get('Id'), e.get('Id'), destination])
                        ncounter = 0
                        nexpr = ""
                if len(nexpr)>0:
                    nexpr = wrapReq(nexpr, 'AA.AuId', destination, 'And')
                    response = sendREQ(nexpr)
                    for e in response.get('entities'):
                        result.append([source, nentity.get('Id'), e.get('Id'), destination])
        #case 1
        expr = ""
        params_dic['count'] = '1'
        expr = wrapReq(expr, 'AA.AuId', destination, 'Or')
        response = sendREQ(expr)
        params_dic['count'] = '1000'
        destEntity = response.get('entities')[0]
        dAAs = destEntity.get('AA')
        if AAs and dAAs:
            for AA in AAs:
                for dAA in dAAs:
                    if dAA.get('AfId') == AA.get('AfId') and dAA.get('AuId') == destination:
                        result.append([source, AA.get('AuId'), AA.get('AfId'), destination])

#start with AuId
else:
    expr = ""
    expr = wrapReq(expr, 'AA.AuId', source, 'Or')
    response = sendREQ(expr)
    entities = response.get('entities')

    #end with Id
    if end == 0:
        expr = ""
        expr = wrapReq(expr, 'Id', destination, 'Or')
        response = sendREQ(expr)
        destEntity = response.get('entities')[0]
        for entity in entities:
            RIds = entity.get('RId')
            Id = entity.get('Id')
            AAs = entity.get('AA')
            Conf = entity.get('C')
            Journal = entity.get('J')
            Fields = entity.get('F')

            #one jump
            if Id == destination:
                result.append([source,destination])

            #two jumps
            if destination in RIds:
                result.append([source, Id, destination])

            #three jumps
            #case 2-5
            if Conf and destEntity.get('C'):
                if Conf.get('CId') == destEntity.get('C').get('CId'):
                    result.append([source, Id, Conf.get('CId'), destination])

            if Journal and destEntity.get('J'):
                if Journal.get('JId') == destEntity.get('J').get('JId'):
                    result.append([source, Id, Journal.get('JId'), destination])

            if Fields and destEntity.get('F'):
                for Field in Fields:
                    for f in destEntity.get('F'):
                        if Field.get('FId') == f.get('FId'):
                            result.append([source, Id, Field.get('FId'), destination])

            if AAs and destEntity.get('AA'):
                for AA in AAs:
                    for dAA in destEntity.get('AA'):
                        if AA.get('AuId') == dAA.get('AuId'):
                            result.append([source, Id, AA.get('AuId'), destination])

        #case 6
        if entities and entities[0].get('AA'):
            AAs = entities[0].get('AA')
            Af = -1
            for AA in AAs:
                if AA.get('AuId') == source:
                    Af = AA.get('AfId')
            for dAA in destEntity.get('AA'):
                if Af and dAA.get('AfId') == Af:
                    result.append([source, Af, dAA.get('AuId'), destination])

        #case 1 bottle neck

        for entity in entities:
            expr = ""
            counter = 0
            RIds = entity.get('RId')
            if RIds:
                for RId in RIds:
                    expr = wrapReq(expr, 'Id', RId, 'Or')
                    counter += 1
                    if counter == MAX_REQ_NUM:
                        expr = wrapReq(expr, 'RId', destination, 'And')
                        response = sendREQ(expr)
                        for newE in response.get('entities'):
                            result.append([source, entity.get('Id'), newE.get('Id'), destination])
                        counter = 0
                        expr  = ""

                if len(expr)>0:
                    expr = wrapReq(expr, 'RId', destination, 'And')
                    response = sendREQ(expr)
                    for newE in response.get('entities'):
                        result.append([source, entity.get('Id'), newE.get('Id'), destination])

    #end with AuId
    else:
        #three jumps    bottle neck
        for entity in entities:
            expr = ""
            counter = 0
            RIds = entity.get('RId')
            if RIds:
                for RId in RIds:
                    expr = wrapReq(expr, 'Id', RId, 'Or')
                    counter += 1
                    if counter == MAX_REQ_NUM:
                        expr = wrapReq(expr, 'AA.AuId', destination, 'And')
                        response = sendREQ(expr)
                        for newE in response.get('entities'):
                            result.append([source, entity.get('Id'), newE.get('Id'), destination])
                        counter = 0
                        expr = ""

                if len(expr)>0:
                    expr = wrapReq(expr, 'AA.AuId', destination, 'And')
                    response = sendREQ(expr)
                    for newE in response.get('entities'):
                        result.append([source, entity.get('Id'), newE.get('Id'), destination])

        #two jumps
        #case 1
        expr = ""
        params_dic['count'] = '1'
        expr = wrapReq(expr, 'AA.AuId', destination, 'Or')
        response = sendREQ(expr)
        params_dic['count'] = '1000'
        destEntity = response.get('entities')[0]
        dAAs = destEntity.get('AA')
        AAs = entities[0].get("AA")
        if AAs and dAAs:
            for AA in AAs:
                for dAA in dAAs:
                    if AA.get('AuId') == source and dAA.get('AfId') == AA.get('AfId') and dAA.get('AuId') == destination:
                        result.append([source, AA.get('AfId'), destination])

        #case 2
        expr = ""
        expr = wrapReq(expr, 'AA.AuId', source, 'And')
        expr = wrapReq(expr, 'AA.AuId', destination, 'And')
        response = sendREQ(expr)
        for e in response.get('entities'):
            result.append([source, e.get('Id'), destination])


print len(result)
print result

conn.close()

####################################