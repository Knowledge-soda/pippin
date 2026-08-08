empty = \{
    [end] = 1
}

con = \([head], [tail]){
    [end] = 0
}

fold = \(f, list, neutral){
    [return] = if(list.end,
               then=neutral,
               else=f(l=list.head, r=fold(f, list.tail, neutral)).return)
}

f = \(l, r){
    [return] = l + r
}


main = \(a){
    [out] = empty.end,
    l = con(5, con(12, con(18, empty))),
    [second] = l.tail.head,
    [sumall] = fold(plus, l, 0)
}
