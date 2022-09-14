# Elpida

The simplest possible messages protocol to connect
a black-box optimization solver with
a black-box optimization problem.

Elpida is designed to be **as simple to use as possible**,
while providing the most common features.
It is oriented toward helping *rigourous benchmarking* of algorithms and problems.

If you now how to read/write to a file and to forge JSON messages,
you should be able to connect the most common problems and solvers,
whatever the programming language or operating system.

<p align="center">
    <img width="500" alt="A tree growing out of a black coffer" src="elpida_emblem.svg" />
</p>

This project provides:

- the definition of the protocol,
- the schema of its messages (useful for validating/debugging),
- examples of messages,
- an example client in Python.


## Protocol

### General Setting

The problem is a server and the solver is a client.
The problem server waits for the solver client to make queries,
at which it will answer a reply.
The message payload is formatted in JSON, following the schema given in the
"Messages" section (see below).


### Message Types

Messages can be either queries, from the (solver) client to the (problem)
server; or replies, from the problem (server) to the solver (client).

A message is a JSON object always holding a `query_type` (string) field.

| `query_type`:| Possible replies:  | Description:
|--------------|--------------------|-------------------------------------------------------------------------------------|
| `new_run`    | `ack` or `error`   | The solver ask for (re)seting the logger state.
| `call`       | `value` or `error` | The solver send a solution and expect its value.
| `stop`       | `ack` or `error`   | The solver ask for the server to stop (probably not enabled on production servers).


### Details

The problem server serves only one problem instance and may expect to be
initialized by a `new_run` query before accepting `call`(s) to its objective
function without returning an `error`.
If the query is well-formed, the server replies with either a `value` or `ack` reply.

The problem server may not implement the `stop` query.


## Basics of Messages

### `call` and `value`

A `call` query holds the solution to be evaluated by the objective function, in
the form of an array of `number`.

Example of a `call` query message:

```json
{
    "query_type":"call",
    "solution": [10,10]
}
```

which would be answered by a reply similar to:

```json
{
    "query_type": "value",
    "value": [3.14]
}
```

Optionaly, the `value` reply can send back the solution.


### Errors

Errors are only emitted from the problem server.

An `error` reply should always provide a description in the `message` (string) field.

Optionally, it can give a `code` (integer), as a unique identifier of the error
type.

Example of error message:
```
{
    "reply_type": "error",
    "message": "Message is ill-formatted",
    "code": 133
}
```

Recommended error types are:

- 133: Payload Parse (the message was ill-formatted and probably do not honor the Schema)
- 134: Payload Type (the server did not expect this query_type)
- 135: Payload Incomplete (required field was missing)
- 136: Dimension Mismatch (the solution does not have the right dimension)
- 137: Solution Mismatch (the solution does not have the correct types of variables)
- 138: Not Supported (an unknown field was in the message)
- 139: Time Out (the objective function computation exceeded time limit)
- 140: Crashed (computation did not complete, but it is believed another attempt can work)
- 141: Aborted (computation did not complete, and it is believed that another attempt would also fail)
- 255: Unknown error


### Metadata fields

All messages have the following optional fields:
- `id` (integer): a unique identifier of the query (in a reply, refers to the related query),
  may be useful for debugging;
- `timestamp` (date-time): date and time of the message;
- `remarks` (string): generic comment (e.g. current experiment).


## Implementation

Theoretically, the message may be transported through any kind of communication
channel, be it a simple file read or a network socket.
The protocol does not enforce anything else than having separated entrypoints for the
queries and the replies.

However, it is recommended to implement the service and client(s) through the
use of special files that are provided by modern operating systems: *named
pipes* (also called *FIFO files*).

Named pipe FIFOs allow to implement synchronous query/reply protocol
by just using regular reads/writes to files.
The operating system implements a blocking mechanism on reads/writes,
which (usually) guarantee that the messages are synchronous.
This also avoid the need for any synchronization code on your side.

Note that modern tools allow to serve the named pipe as a network socket (see
below).

In practice, there is one named pipe for queries (in which the client writes and the server
reads) and one for replies (in which the server writes and the client reads).

On POSIX OS (Linux or MacOS), you can create named FIFO pipes
with the `mkfifo` command.

On Windows, things are more convoluted as the OS supports named pipes
but does not provide a simple command for creating them.
You may try some of the
[solutions proposed on Stack Overflow](https://stackoverflow.com/questions/3670039/is-it-possible-to-open-a-named-pipe-with-command-line-in-windows).


### Minimal solver client

The recommended implementation is simple as it just consists in writing in a
`query` file and reading from a `reply` file, just as you would do with regular files.

The simplest client, making a single query, can be written in Python as:

```python
import json

# Forge a JSON `call` query:
squery = json.dumps( {"query_type":"call", "solution":[0,1,1,0,1]} )

# Send it to the server:
with open("query",'w') as fd:
    fd.write(squery)

# Wait for the answer and read it when it's available:
with open("reply",'r') as fd:
    sreply = fd.read()

# Decode the JSON:
jreply = json.loads(sreply)

# Extract the objective function values:
values = jreply["value"] # This is a list.
```

An example implementation of a solver client is given in Python in
`examples/python/solver_client.py`.


### Minimal problem server

The recommended implementation is simple as it just consists in reading from a
`query` file and writing in a `reply` file, just as you would do with regular files.

The simplest problem server, answering a single query, can be written in Python as:

```python
import json

# Wait for a query:
with open("query",'r') as fd:
    squery = fd.read()

# Parse the message:
jquery = json.loads(squery)

# Extract the solution:
sol = jquery["solution"]

# Compute the value of the objective function:
val = sum(sol)

# Forge a JSON `value` reply:
sreply = json.dumps( { "query_type":"value", "value":[val] } )

# Send the reply:
with open("reply",'w') as fd:
    fd.write(sreply)
```

An example implementation of a problem server is given in Python in
`examples/python/problem_server.py`.


## More on Messages

### queries

#### `new_run`

Example of minimal `new_run` query:

```json
{
    "query_type": "new_run",
    "algorithm": "MyCMA",
    "version": "3.1.4"
}
```

Example of a complete `new_run` query:

```json
{
    "query_type": "new_run",
    "algorithm": "CMA-ES",
    "implementation": "Paradiseo-EDO",
    "version": "104d5dc71",
    "parameters": [
        {"name": "inertia",    "value": 1.2},
        {"name": "covar_init", "value": [1,2,3,4]},
        {"name": "covar_dim",  "value": 2}
    ],
    "id": 1,
    "timestamp": "2022-06-02T11:41:01+02:00Z",
    "remarks": "preliminary test",
}
```


#### `call`

Example of minimal `call` query:

```json
{
    "query_type":"call",
    "solution": [10,10]
}
```

Example of a complete `call` query:

```json
{
    "query_type": "call",
    "solution": [10,10],
    "state": [
        {"name": "step_size",         "value": 1.2},
        {"name": "covariance_matrix", "value": [1,2,3,4]},
        {"name": "covar_dim",         "value": 2}
    ],
    "id": 1,
    "timestamp": "2021-12-21T13:40:31-01:00Z",
    "remarks": "Ran on node #05 of the cluster"
}
```


### Replies

#### `ack`

Example of a minimal `ack` reply:

```json
{
    "reply_type": "ack"
}
```


Example of a complete `ack` reply:

```json
{
    "reply_type": "ack",
    "id": 1,
    "timestamp": "2021-12-21T13:40:31-01:00Z",
    "remarks": "Reply to `new_run` query #1"
}
```


#### `value`

Example of a minimal `value` reply:

```json
{
    "reply_type": "value",
    "value": [1.0696e6]
}
```

Example of a complete `value` reply:

```json
{
    "reply_type": "value",
    "value": [123.456, 7.89],
    
    "solution": [0,1,1,0],
    "id": 12345,
    "timestamp": "2021-12-21T12:21:12-00:00",
    "remarks": "Ran on node #12 of the cluster"
}
```

#### `error`


Example of a minimal `error` reply:

```json
{
    "reply_type": "error",
    "message": "ERROR: unknown error."
}
```

Example of a complete `error` reply:

```json
{
    "reply_type": "error",
    "message": "Message is ill-formatted",
    "code": 133,
    "id": 12345,
    "timestamp": "2021-12-21T12:21:12-00:00",
    "remarks": "Here are the details of the error returned by the parser: "
}
```


### Fundamentals of Pipes

Named pipes are special files with blocking input/output, which means that a
process reading such a file will be suspended until there is something to read.
This allows for very simple I/O code, avoiding polling and complex network
management: all you have to do to implement a client is to write the query in
the query file, then read the reply in the reply file.
The execution will advance only when the reply have been written in the file.

The theoretical principle can be represented by this UML sequence diagram:

```
            Named pipes
         ┌───────┴───────┐
┌──────┐ ┌─────┐   ┌─────┐ ┌──────┐
│Client│ │reply│   │query│ │Server│
└───┬──┘ └─┬───┘   └─┬───┘ └───┬──┘
    │      │         │         │
    │      │         │  ┌──────╢
    │      │    block│  │ wait ║
    │query │         │  └─────>║
    ├───────────────>│         │
    ╟─────┐│         ├────────>│
    ║wait ││block    │         ║process
    ║<────┘│         │         ║
    │      │<──────────────────┤
    │<─────┤         │    reply│
    │      │         │         │
    ┊      ┊         ┊         ┊
```

Note that the service should be started first, waiting for the input.


## Going further

### Validate messages

The formal description of a queries is available in
`elpida-query.schema.yaml`, the one for replies in `elpida-reply.schema.yaml`.

The description follows the [JSON Scehma format (draft
07)](http://json-schema.org/draft-07/schema), but is presented in the
(strictly equivalent) YAML format, easier to read for humans and allowing for
comments.

One can validate any message against those schema, using the
[Apptainer](https://apptainer.org)
container defined by `message_validator.apptainer.def`.
To build this container,
install apptainer and run `apptainer build message_validator.sif
message_validator.apptainer.def`.
To validate a message simply run: `apptainer run message_validator.sif
<schema.yaml> <message.json>`.

As with all container systems, Apptainer needs a Linux machine.
If you are on another OS, you may use a virtual machine.
We recommend you install an Ubuntu virtual machine
using [Multipass](https://multipass.run/), on which it is easy to install Apptainer.

Note that it is not mandatory to formally validate message to use the Elpida
protocol, but we strongly recommend you include a validation feature for your
client or service, at least in debug mode.


### Network gateway

If you want to expose such a service as a network server, just use socat.

For example, to get _data_ query from the network for `service1`:

```sh
socat -v -u TCP-LISTEN:8423,reuseaddr PIPE:./query
```

You can test it by sending something on the connection:

```sh
echo "Hello World!" > /dev/tcp/127.0.0.1/8423
```

Conversely, to send automatically back the answer to some server:

```sh
socat -v -u PIPE:./reply TCP2:8424:host
```

Be aware that `socat` will terminate as soon as it receives the end of the message.
Thus, if you want to establish a permanent gate, you will have to use the `fork`
option:

```sh
socat TCP-LISTEN:8478,reuseaddr,fork PIPE:/./query
```

# About

The Elpida protocol idea arised jointly in the [IEEE Task Force on "Automated Algorithm Design, Configuration and Selection"](https://sites.google.com/view/ieeeaadcs/home), and in the ["Benchmarked: Optimization Meets Machine Learning"](https://www.lorentzcenter.nl/benchmarked-optimization-meets-machine-learning.html) workshop.

The name "Elpida" means "hope/expectation" in greek (ελπίδα), as a reference to what remain in the (black) "box" in the *Pandora* tale of the ancient greek mythology.
