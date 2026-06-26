#include<stdlib.h>
#include<stdbool.h>
#include<string.h>
#include<stdio.h>

// NODE type definition
typedef enum {
    NUMBER,
    BIFUNC,
    FUNC,
    APPL,
    PROP,
    NAME,
    NONE
} NodeType;

typedef struct Node Node;

// auxiliary typedefs
typedef struct Pair {
    char *name;
    Node *value;
} Pair;

typedef struct Pairs {
    size_t len;
    Pair *data;
} Pairs;

typedef struct AppPair {
    bool numeric;
    union {
        size_t index;
        char *name;
    } name;
    Node *value;
} AppPair;

typedef struct AppPairs {
    size_t len;
    AppPair *data;
} AppPairs;

typedef Node* (*unary)(Pairs args);

// main typedefs
typedef struct {
    int value;
} Number;

typedef struct {
    unary code;
} BuiltInFunction;

typedef struct {
    Pairs results, args;
    bool changed;
} Function;

typedef struct {
    Node *func;
    AppPairs args;
} Application;

typedef struct {
    Node *left;
    char *name;
} Propery;

typedef struct {
    char *str;
} Name;

// Node definition
struct Node {
    NodeType type;
    Node *clone;
    union {
        Number num;
        BuiltInFunction bfunc;
        Function func;
        Application appl;
        Propery prop;
        Name name;
    } data;
};

// Debug
void debug_print_node(Node *node){
    printf("%p type=%i", node -> clone, node -> type);
    switch (node -> type){
            case NUMBER:
                printf(" value=%i", (node -> data).num.value);
                break;
            case BIFUNC:
                printf(" code=%p", (node -> data).bfunc.code);
                break;
            case FUNC:
                printf(" changed=%i, results.len=%lu, results.data=%p, "
                        "args.len=%lu, args.data=%p",
                        (node -> data).func.changed,
                        (node -> data).func.results.len,
                        (node -> data).func.results.data,
                        (node -> data).func.args.len,
                        (node -> data).func.args.data);
                break;
            case NAME:
                printf(" str=%s", (node -> data).name.str);
                break;
            case APPL:
                printf(" func=%p, args.len=%lu, args.data=%p",
                        (node -> data).appl.func,
                        (node -> data).appl.args.len,
                        (node -> data).appl.args.data
                        );
                break;
            case PROP:
                printf(" name=%s, left=%p", (node -> data).prop.name,
                        (node -> data).prop.left);
                break;
            case NONE:
                printf(" NONE");
    }
}

#define DEBUG_PRINT(NODE) \
    printf("DEBUG %s:%i - ", __func__, __LINE__); \
    debug_print_node(NODE); \
    printf("\n")

// Constructors
Node *create_number(int n){
    Node *ret = malloc(sizeof(Node));
    ret -> type = NUMBER;
    ret -> clone = NULL;
    (ret -> data).num.value = n;
    return ret;
}

Node *create_built_in(unary code){
    Node *ret = malloc(sizeof(Node));
    ret -> type = BIFUNC;
    ret -> clone = NULL;
    (ret -> data).bfunc.code = code;
    return ret;
}

void set_up_func(Node *ret, size_t expect_args, size_t number_of_returns){
    ret -> type = FUNC;
    ret -> clone = NULL;
    (ret -> data).func.args.data = malloc(sizeof(Pair) * expect_args);
    (ret -> data).func.args.len = 0;
    (ret -> data).func.results.data = malloc(sizeof(Pair) * number_of_returns);
    (ret -> data).func.results.len = 0;
}

Node *create_func(size_t expect_args, size_t number_of_returns){
    Node *ret = malloc(sizeof(Node));
    set_up_func(ret, expect_args, number_of_returns);
    (ret -> data).func.changed = false;
    return ret;
}

void set_func_arg(Node *func, char *name){
    Pair *args = (func -> data).func.args.data;
    size_t len = (func -> data).func.args.len;
    args[len].name = name;
    args[len].value = NULL;
    ((func -> data).func.args.len)++;
}

void set_func_res(Node *func, char *name, Node *res){
    Pair *returns = (func -> data).func.results.data;
    size_t len = (func -> data).func.results.len;
    returns[len].name = name;
    returns[len].value = res;
    ((func -> data).func.results.len)++;
}

Node *create_application(Node *func, size_t number_of_arguments){
    Node *ret = malloc(sizeof(Node));
    ret -> type = APPL;
    ret -> clone = NULL;
    (ret -> data).appl.func = func;
    (ret -> data).appl.args.data = malloc(sizeof(AppPair) * number_of_arguments);
    (ret -> data).appl.args.len = 0;
    return ret;
}

void set_appl_arg_str(Node *appl, char *name, Node *res){
    AppPair *returns = (appl -> data).appl.args.data;
    size_t len = (appl -> data).appl.args.len;
    returns[len].name.name = name;
    returns[len].value = res;
    returns[len].numeric = false;
    ((appl -> data).appl.args.len)++;
}

void set_appl_arg_num(Node *appl, size_t i, Node *res){
    AppPair *returns = (appl -> data).appl.args.data;
    size_t len = (appl -> data).appl.args.len;
    returns[len].name.index = i;
    returns[len].value = res;
    returns[len].numeric = true;
    ((appl -> data).appl.args.len)++;
}

Node *create_property(Node *left, char *name){
    Node *ret = malloc(sizeof(Node));
    ret -> type = PROP;
    ret -> clone = NULL;
    (ret -> data).prop.name = name;
    (ret -> data).prop.left = left;
    return ret;
}

Node *create_name(char *str){
    Node *ret = malloc(sizeof(Node));
    ret -> type = NAME;
    ret -> clone = NULL;
    (ret -> data).name.str = str;
    return ret;
}

// important declarations
Node *clone(Node *old, Pairs args);
Node *eval(Node *node);

// auxiliary functions
void find_rl_arguments(Pairs args, Node **left, Node **right){
    for (size_t i = 0;i < args.len;i++){
        if (args.data[i].name[0] == 'l' &&
            args.data[i].name[1] == '\0' &&
            args.data[i].value){
            *left = eval(args.data[i].value);
        }
        if (args.data[i].name[0] == 'r' &&
            args.data[i].name[1] == '\0' &&
            args.data[i].value){
            *right = eval(args.data[i].value);
        }
    }
}

void absorb(Node *lhs, Node *rhs){
    lhs -> type = rhs -> type;
    lhs -> clone = NULL;
    lhs -> data = rhs -> data;
}

Node *shallow_clone(Node *old){
    Node *ret = malloc(sizeof(Node));
    ret -> type = old -> type;
    ret -> clone = NULL;
    ret -> data = old -> data;
    old -> clone = ret;
    return ret;
}

Node *deep_clone_property(Node *prop, Pairs args){
    Node *ret = malloc(sizeof(Node));
    ret -> type = PROP;
    ret -> clone = NULL;
    (ret -> data).prop.left = clone((prop -> data).prop.left, args);
    (ret -> data).prop.name = (prop -> data).prop.name;
    prop -> clone = ret;
    return ret;
}

Node *deep_clone_application(Node *appl, Pairs args){
    Node *ret = malloc(sizeof(Node));
    ret -> type = APPL;
    ret -> clone = NULL;
    (ret -> data).appl.func = clone((appl -> data).appl.func, args);

    size_t len = (appl -> data).appl.args.len;
    AppPair *old_data = (appl -> data).appl.args.data;
    AppPair *new_data = malloc(sizeof(AppPair) * len);
    for (size_t i = 0;i < len;i++){
        if (old_data[i].numeric){
            new_data[i].name.index = old_data[i].name.index;
        } else {
            new_data[i].name.name = old_data[i].name.name;
        }
        new_data[i].numeric = old_data[i].numeric;
        new_data[i].value = clone((appl -> data).appl.args.data[i].value, args);
    }
    (ret -> data).appl.args.len = len;
    (ret -> data).appl.args.data = new_data;
    appl -> clone = ret;
    return ret;
}

Node *get_argument(Node *arg, Pairs args){
    for (size_t i = 0;i < args.len;i++){
        if (!strcmp((arg -> data).name.str, args.data[i].name)
            && args.data[i].value)
            return args.data[i].value;
    }
    return shallow_clone(arg); // shallow_clone??
}

Node *clone(Node *old, Pairs args){
    if (old -> clone)
        return old -> clone;
    switch (old -> type){
        case NUMBER:
        case NONE:
            return old;
        case BIFUNC:
            return (old -> clone = (old -> data).bfunc.code(args));
        case FUNC:
            return (old -> clone = shallow_clone(old));
        case APPL:
            return (old -> clone = deep_clone_application(old, args));
        case PROP:
            return (old -> clone = deep_clone_property(old, args));
        case NAME:
            {
            Node *ret = get_argument(old, args);
            old -> clone = ret;
            return ret;
            }
    }
}

void end_cloning(Node *node){
    if (!node -> clone)
        return;
    node -> clone = NULL;
    switch (node -> type){
        case NONE:
        case NUMBER:
        case BIFUNC:
        case FUNC:
        case NAME:
            break;
        case APPL:
            end_cloning((node -> data).appl.func);
            for (size_t i = 0;i < (node -> data).appl.args.len;i++){
                end_cloning((node -> data).appl.args.data[i].value);
            }
            break;
        case PROP:
            end_cloning((node -> data).prop.left);
            break;
    }
}

// built-ins

Node *sum(Pairs args){
    Node *left = NULL, *right = NULL;
    find_rl_arguments(args, &left, &right);
    if (left == NULL || right == NULL)
        return create_number(0);
    return create_number((left -> data).num.value + (right -> data).num.value);
}

Node *mult(Pairs args){
    Node *left = NULL, *right = NULL;
    find_rl_arguments(args, &left, &right);
    if (left == NULL || right == NULL)
        return create_number(0);
    return create_number((left -> data).num.value * (right -> data).num.value);
}

Node *minus(Pairs args){
    Node *left = NULL, *right = NULL;
    find_rl_arguments(args, &left, &right);
    if (left == NULL || right == NULL)
        return create_number(0);
    return create_number((left -> data).num.value - (right -> data).num.value);
}

Node *divide(Pairs args){
    Node *left = NULL, *right = NULL;
    find_rl_arguments(args, &left, &right);
    if (left == NULL || right == NULL)
        return create_number(0);
    return create_number((left -> data).num.value / (right -> data).num.value);
}

Node *if_node(Pairs args){
    bool select = false;
    for (size_t i = 0;i < args.len;i++){
        if (!strcmp(args.data[i].name, "cond")){
            Node *tmp = eval(args.data[i].value);
            select = (tmp -> data).num.value;
        }
    }
    char *get = select ? "then" : "else";
    for (size_t i = 0;i < args.len;i++){
        if (!strcmp(args.data[i].name, get)){
            return eval(args.data[i].value);
        }
    }
    return NULL;
}

Node *create_rl_built_in(unary code){
    Node *ret = create_func(2, 1);
    set_func_arg(ret, "l");
    set_func_arg(ret, "r");
    Node *res = create_built_in(code);
    set_func_res(ret, "return", res);
    return ret;
}

Node *create_if_built_in(unary code){
    Node *ret = create_func(3, 1);
    set_func_arg(ret, "cond");
    set_func_arg(ret, "then");
    set_func_arg(ret, "else");
    Node *res = create_built_in(code);
    set_func_res(ret, "return", res);
    return ret;
}

void add_pairs(Pairs from, Pairs *to){
    for (size_t i = 0;i < from.len;i++){
        (to -> data)[to -> len] = from.data[i];
        (to -> len)++;
    }
}

size_t find_arg(Pairs args, AppPair arg){
    if (arg.numeric){
        size_t index = arg.name.index;
        for (size_t ret = 0;ret < args.len;ret++){
            if (!args.data[ret].value){
                if (index) index--;
                else return ret;
            }
        }
    } else {
        for (size_t ret = 0;ret < args.len;ret++){
            if (!strcmp(args.data[ret].name, arg.name.name))
                return ret;
        }
    }
    return 0;
    // TODO: out of bounds error
}

void apply(Node *ret, Node *func, AppPairs applications){
    set_up_func(ret, (func -> data).func.args.len + applications.len,
                     (func -> data).func.results.len);
    (ret -> data).func.changed = true;
    add_pairs((func -> data).func.args, &(ret -> data).func.args);
    size_t indexes[applications.len];
    for (size_t i = 0;i < applications.len;i++){
        indexes[i] = find_arg((func -> data).func.args, applications.data[i]);
    }
    for (size_t i = 0;i < applications.len;i++){
        (ret -> data).func.args.data[indexes[i]].value = applications.data[i].value;
    }
    add_pairs((func -> data).func.results, &(ret -> data).func.results);
}

Node *function_get(Node *func, char *name){
    Pairs results = (func -> data).func.results;
    if ((func -> data).func.changed){
        Node *old[results.len];
        for (size_t i = 0;i < results.len;i++){
            old[i] = results.data[i].value;
            results.data[i].value = clone(results.data[i].value,
                (func -> data).func.args);
        }
        (func -> data).func.changed = false;
        for (size_t i = 0;i < results.len;i++){
            end_cloning(old[i]);
            end_cloning(results.data[i].value);
        }
    }

    for (size_t i = 0;i < results.len;i++){
        if (!strcmp(results.data[i].name, name))
            return results.data[i].value;
    }
    return NULL;
}

Node *eval(Node *node){
    bool run = true;
    while (run){
        switch (node -> type){
            case NONE:
            case NUMBER:
            case BIFUNC:
            case FUNC:
            case NAME:
                run = false;
                break;
            case APPL:
                {
                eval((node -> data).appl.func);
                Node tmp;
                apply(&tmp, (node -> data).appl.func, (node -> data).appl.args);
                absorb(node, &tmp);
                break;
                }
            case PROP:
                eval((node -> data).prop.left);
                Node *tmp = function_get((node -> data).prop.left, (node -> data).prop.name);
                absorb(node, tmp);
                break;
        }
    }
    return node;
}

void print(Node *node){
    switch (node -> type){
            case NUMBER:
                printf("%i\n", (node -> data).num.value);
                break;
            case BIFUNC:
                printf("Result is unprintable (BIFUNC)\n");
                break;
            case FUNC:
                printf("Result is unprintable (FUNC)\n");
                break;
            case NAME:
                printf("Result is unprintable (NAME)\n");
                break;
            case APPL:
                printf("Result is unprintable (APPL)\n");
                break;
            case PROP:
                printf("Result is unprintable (PROP)\n");
                break;
            case NONE:
                printf("Result is unprintable (NONE)\n");
                break;
    }
}

size_t presplit(char *str, int *num){
    size_t ret = 0;
    for (;str[ret] != '=';ret++);
    str[ret] = '\0';
    sscanf(str + ret + 1, "%i", num);
    return ret;
}

Node *create_one_apply(Node *func, char *var, int num){
    Node *num_node = create_number(num);
    Node *res = create_application(func, 1);
    set_appl_arg_str(res, var, num_node);
    return res;
}

AppPair create_single_pair(char *var, int num){
    Node *num_node = create_number(num);
    return (AppPair) {.name.name = var, .value = num_node, .numeric = false};
}

void apply_one(Node *node, AppPair pair){
    size_t index = find_arg((node -> data).func.args, pair);
    (node -> data).func.args.data[index].value = pair.value;
    (node -> data).func.changed = true;
}

void driver(Node *node){
    char input[256];
    while (true){
        fgets(input, 256, stdin);
        for (size_t i = 0;;i++){
            if (input[i] == '\n'){
                input[i] = '\0';
                break;
            }
        }
        if (input[0] == '!'){
            break;
        } else if (input[0] == '?'){
            Node *ret = function_get(node, input + 1);
            eval(ret);
            print(ret);
        } else {
            int num;
            char *str = malloc(sizeof(char) * (presplit(input, &num) + 1));
            strcpy(str, input);
            apply_one(node, create_single_pair(str, num));
        }
    }
}
