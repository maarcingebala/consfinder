function(doc) {
    var results = {'timestamp': doc.timestamp, 'params': doc.params};
    for (key in doc.consistency) {
        results[key] = doc.consistency[key];
    }
    for (key in doc.consensus) {
        results[key] = doc.consensus[key];
    }
    emit([doc['params']['length'], doc['params']['n']], results);
}


// dla euclidean
// 
// function(doc) {
//     var results = {'timestamp': doc.timestamp, 'params': doc.params};
//     for (key in doc.consistency) {
//         results[key] = doc.consistency[key];
//     }
//     for (key in doc.consensus) {
//         results[key] = doc.consensus[key];
//     }
//     emit([doc['params']['n']], results);
// }