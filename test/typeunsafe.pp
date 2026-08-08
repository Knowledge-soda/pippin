apply_f = \(f, x){
    [y] = f(x=x).return
}

g = \(x){
    [return] = x * x
}

main = \(a){
    [out] = apply_f(f=g, x=a).y
}
