import { RelationList } from './RelationList.jsx';

/** Child records belong to the parent and are created through their own form, so this stays remove-only. */
export function One2manyField(props) {
    return <RelationList {...props} allowAdd={false} />;
}
