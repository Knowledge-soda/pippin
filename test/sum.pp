square = (a){
    [r] = *(l=a, r=a)
}

main = (x){
    [s] = +(l=square(a=x).r, r=square(a=+(l=x, r=1)).r)
}
