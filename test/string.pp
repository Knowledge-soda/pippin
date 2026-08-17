len = \(str){
    [return] = if(strempty(str),
        then=0,
        else=1 + len(strtail(str)))
}

main = \(name){
    [help] = "nesto",
    [first] = strhead(name),
    [rest] = strtail(name),
    [l] = len(name)
}
