turtle = \([x], [y], [heading]){
    [up] = 0, [right] = 1, [down] = 2, [left] = 3,
    [forward] = \(n){
        new_y = y - n * if(equal(heading, left),
            then=0, else=heading - 1),
        new_x = x - n * if(equal(heading, up),
            then=0, else=heading - 2),
        [new] = turtle(new_x, new_y, heading)
    },
    [turn_right] = turtle(x, y,
        if(equal(heading, left), then=up, else=heading+1)),
    [turn_left] = turtle(x, y,
        if(equal(heading, up), then=left, else=heading-1))
}

empty = \{
    [debug] = "empty",
    [execute] = \(t){[new] = t}
}

forward = \(n){
    [debug] = "forward",
    [execute] = \(t){[new] = t.forward(n).new}
}

left = \{
    [debug] = "left",
    [execute] = \(t){[new] = t.turn_left}
}

right = \{
    [debug] = "right",
    [execute] = \(t){[new] = t.turn_right}
}

repeat = \(n, list){
    [execute] = \(t){
        lex = list.execute(t),
        [new]= if(equal(n, 1), then=lex,
            else=repeat(n - 1, list).execute(lex.new)).new
    },
    [debug] = "repeat"
}

command_list = \([head], [tail]){
    [execute] = \(t){
        [new] = tail.execute(head.execute(t).new).new
    },
    [debug] = "command_list"
}

parse_single = \(text){
    is_open = equal(strhead("("), char),
    is_forward = equal(strhead("f"), char),
    is_backward = equal(strhead("b"), char),
    is_left = equal(strhead("l"), char),
    is_right = equal(strhead("r"), char),
    is_digit = geq(char, strhead("0")) * leq(char, strhead("9")),
    char = strhead(text),
    nextcmd = parse_single(tail),
    block = parse(tail),
    tail = strtail(text),
    [cmd] = if(is_left, then=left,
        else=if(is_right, then=right,
        else=if(is_forward, then=forward(1),
        else=if(is_backward, then=forward(0-1),
        else=if(is_digit, then=repeat(char - strhead("0"), nextcmd.cmd),
        else=if(is_open, then=block.cmds,
        else=empty)))))),
    [rest] = if(is_digit, then=nextcmd.rest,
        else=if(is_open, then=block.rest,
        else=tail))
}

parse = \(text){
    is_closed = equal(strhead(")"), strhead(text)),
    last = if(strempty(text), 1, is_closed),
    [cmds] = if(last,
        then=empty,
        else=command_list(head.cmd, new.cmds)),
    [rest] = if(strempty(text),
        then=text,
        else=if(is_closed, then=strtail(text), else=new.rest)),
    new = parse(head.rest),
    head = parse_single(text)
}

main = \(text){
    cmds = parse(text).cmds,
    t0 = turtle(0, 0, turtle.up),
    newt = cmds.execute(turtle(0, 0, turtle.up)).new,
    newt2 = cmds.head.execute(t0).new,
    [dbg] = cmds.tail.head.debug,
    [nx] = newt.x,
    [ny] = newt.y
}
