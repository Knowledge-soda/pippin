square = \(a){
    [r] = a * a
}

# comment

#{
Multiline
comment
}#

main = \(x){
    #{
        this
        #{
            allows
        }#
        Nesting
    }#
    [s] = square(x).r + square(x + 1).r
}
