# pyCimabue

## Experimental distributed middleware with fault-tolerance and QoS

I wanted to investigate the problem of fault-tolerance for distributed middleware: *pyCimabue* is the result if this.

It implements a messaging system based on a client-server architecture. Clients connect to the server through a Proxy, so the actual server is transparent. Behind the proxy, there's a network of servers: one of them acts as a *master* (i.e. provides the service), another one is a *backup* and the rest are *slaves*. The backup server monitors the master and, in case of failures, elects a new master among the slaves using an election protocol. At the same time, the master monitors the backup server, electing a new one as needed. All this process is transparent to clients.

Being a study on fault-tolerance and election protocols, I deliberately avoided to add features such as load balancing, parallel processing, authentication, etc. This is not meant to be production code, but it gave me good marks when I presented it as a Uni project :)

#### Trivia

My first implementation was in C++ and I named it *Cimabue*, after the [famous Italian painter](http://en.wikipedia.org/wiki/Cimabue). However I decided to adopt Python for fast prototyping: this is why I added the *py* suffix.