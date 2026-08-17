struct = \{
    [x] = 10,
    [y] = 2,
    [z] = "hello"
}

main = \(name){
    [out] = get(struct, name)
}
