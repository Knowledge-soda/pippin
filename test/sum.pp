square = (a){
    [r] = *(l=a, r=a)
}

# comment

#{
Multiline
comment
}#

main = (x){
    #{
        this
        #{
            allows
        }#
        Nesting
    }#
    [s] = +(l=square(a=x).r, r=square(a=+(l=x, r=1)).r)
}
