intparse = \(str, left){
    zero = strhead("0"),
    [return] = if(strempty(str),
        then=left,
        else=intparse(strtail(str),
            left = strhead(str) - zero + 10 * left))
}

convert = \(str){
    [head] = strhead(str),
    [tail] = convert(strtail(str)),
    [end] = strempty(str)
}

isdigit = \(d){
    [return] = geq(d, strhead("0")) * leq(d, strhead("9"))
}

intparse2 = \(str, left){
    zero = strhead("0"),
    head = strhead(str),
    last = if(strempty(str), then=strempty(str), else=1-isdigit(head)),
    next = intparse2(tail, left = head - zero + 10 * left),
    tail = if(strempty(str), then=str, else=strtail(str)),
    [number] = if(last,
        then=left,
        else=next.number),
    [rest] = if(last,
        then=tail,
        else=next.rest)
}

listparse = \(str){
    [end] = strempty(str),
    parse = intparse2(str, 0),
    [head] = parse.number,
    [tail] = listparse(parse.rest)
}

fold = \(f, list, neutral){
    [return] = if(list.end,
               then=neutral,
               else=f(l=list.head, r=fold(f, list.tail, neutral)).return)
}

main = \(text, list){
    [n] = intparse(text, 0),
    [sum] = fold(plus, listparse(list), 0)
}
