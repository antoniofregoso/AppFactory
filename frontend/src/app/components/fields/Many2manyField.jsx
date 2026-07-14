import { RelationList } from './RelationList.jsx';

export function Many2manyField(props) {
    return <RelationList {...props} allowAdd />;
}
