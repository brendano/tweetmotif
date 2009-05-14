import operator

def kmpTable(lst):
    t = []
    i = 0
    j = -1
    t.append(j) # i.e., t[-1 +1]
    lst_j = None
    while i < len(lst):
        if lst[i] == lst_j:
            t.append(j + 1) # i.e., t[i +1]
            j += 1
            i += 1
        elif j > 0: 
            j = t[j - 1 +1]
        else:
            t.append(0) # i.e., t[i +1]
            i += 1
            j = 0
        lst_j = lst[j]
    return t

def indexSubsequence(subsequence, sequence, start=-1, cmpFn=operator.eq):
    # KMP
    t = kmpTable(subsequence)
    i = m = 0
    while m < start:
        m += 1
    while i < len(subsequence) and m + i < len(sequence):
        if cmpFn(subsequence[i], sequence[m + i]):
            i += 1
        else:
            m += i - t[i - 1 +1]
            if i > 0:
                i = t[i - 1 +1]
    if i == len(subsequence):
        return m
    else:
        return -1

def isSubseq(subseq, seq):
  return indexSubsequence(subseq, seq) != -1