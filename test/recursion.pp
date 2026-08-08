factorial = \(n){
    [return] = if(n,
        then=factorial(n - 1) * n,
        else=1)
}

fibbonaci = \(n){
    [return] = if(n,
        then=if(n - 1,
            then=fibbonaci(n - 1) + fibbonaci(n - 2),
            else=1),
        else=0)
}

fib2 = \(n){
    last = fib2(n - 1),
    [prev] = if(n - 1,
        then=last.now,
        else=0),
    [now] = if(n - 1,
        then=last.prev + last.now,
        else=1)
}

main = \(n){
    [fact] = factorial(n),
    [fib] = fibbonaci(n),
    [fibalt] = fib2(n).now
}
